#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This submodule runs all parsers to get a days worth of data.

The Forecast class basically follows all of the steps in the package
description in the README with a couple of minor variations:

-If fresh_install is passed as True, the install process is started
-If test is passed as true, all but one prefix is deleted from the mrt
 announcements. This makes the extrapolator run much faster, and is for
 tests only.
-db.vacuum_analyze_checkpoint is called 3 times. Once before joining the
 mrt announcements with roas, once before running the what if analysis,
 and at the end of everything. The purpose of this is to save storage
 space, create statistics on all of the tables, and write to disk. This
 helps the query planner when planning table joins and massively
 decreases runtime.

Again, this module is too hard to explain in a docstring, please refer
to the https://github.com/jfuruness/lib_bgp_data#package-description

Design Choices:
-Nothing is multithreaded for simplicity of code, and since each parser
 either takes up all the threads or takes <1 minute
-The database is vacuum analyzed and checkpointed before big joins to
 help the query planner choose the right query plan
-When testing only one prefix is used to reduce data size and speed up
 extrapolator

Possible Future Extensions:
-Unit tests
-Cmd line args
-Docs on both
"""

from ..relationships_parser import Relationships_Parser
from ..roas_collector import ROAs_Collector
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..mrt_parser import MRT_Parser
from ..extrapolator import Extrapolator
from ..rpki_validator import RPKI_Validator
from ..what_if_analysis import What_If_Analysis
from ..utils import utils, Database, db_connection, Install, error_catcher
from .tables import MRT_W_Roas_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Forecast:
    """This class contains all the neccessary parsing functions"""

    @error_catcher()
    def __init__(self, forecast_args={}):
        """Initializes paths and logger."""

        utils.set_common_init_args(self, forecast_args),

    @utils.run_parser()
    @error_catcher()
    def run_forecast(self,
                     start=utils.get_default_start(),
                     end=utils.get_default_end(),
                     fresh_install=False,
                     mrt_args={},
                     mrt_parse_args={},
                     rel_args={},
                     rel_parse_args={},
                     roas_args={},
                     web_args={},
                     web_parse_args={},
                     exr_args={},
                     rpki_args={},
                     what_if_args={},
                     test=False):

        self.logger.info("Running from {} to {} in UTC".format(start, end))

        if fresh_install:
            Install().install(fresh_install)
        # First we want to parse the mrt files and create the index
        # This uses all the threads, so no need to multithread
        MRT_Parser(mrt_args).parse_files(start, end, **mrt_parse_args)
        # Then we get the relationships data. We aren't going to run this
        # multithreaded because it is so fast, there is no point
        Relationships_Parser(rel_args).parse_files(**rel_parse_args)
        # Now lets get roas, its fast so no multiprocessing
        ROAs_Collector(roas_args).parse_roas()
        # Get hijack data. The first time takes a while
        BGPStream_Website_Parser(web_args).parse(start, end, **web_parse_args)

        with db_connection(Database, self.logger) as _db:

            # Used for testing to significantly reduce extrapolator runtime
            if test:
                sql = """DELETE FROM mrt_announcements
                      WHERE prefix != '1.0.0.0/24';"""
                _db.execute(sql)

            # Cleans up the database
            _db.vacuum_analyze_checkpoint()

        # Only keep announcements covered by a roa
        # drops old table, unhinges db, performs query, rehinges db
        with db_connection(MRT_W_Roas_Table, self.logger) as _db:
            _db.vacuum_analyze_checkpoint()

            # Runs the extrapolator and creates the neccessary indexes
            Extrapolator(exr_args).run_forecast(_db.name)

            # Runs the rpki validator and stores data in db
            RPKI_Validator(rpki_args).run_validator()

            # Cleans up db and performs statistics for what if joins
            _db.vacuum_analyze_checkpoint()

            # Runs the what if analysis
            What_If_Analysis(what_if_args).run_rov_policy()

            # Rewrites the whole database for storage
            _db.vacuum_analyze_checkpoint(full=True)

        self.logger.info("Ran from {} to {} in UTC".format(start, end))
