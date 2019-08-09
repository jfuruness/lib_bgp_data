#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains all parsers neccessary to parse bgp data

This also contains all the functions to run each individual parser.
The main function of this script, is to run all of these jobs in
the proper order with the proper settings. This can be run as a chron
job"""
# future improvement: improving logging (can literally replace the logging class)
from multiprocessing import Process
from subprocess import Popen, PIPE
from ..relationships_parser import Relationships_Parser
from ..roas_collector import ROAs_Collector
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..mrt_parser import MRT_Parser
from ..extrapolator import Extrapolator
from ..rpki_validator import RPKI_Validator
from ..what_if_analysis import What_If_Analysis
from ..utils import utils, Database, db_connection, Install
from .tables import MRT_W_Roas_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Forecast:
    """This class contains all the neccessary parsing functions"""

#    @utils.run_parser()
    def __init__(self, forecast_args):
        """Initializes paths and logger."""

        utils.set_common_init_args(self, forecast_args),

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
                     what_if_args={},
                     what_if_parse_args={},
                     rpki_args={},
                     rpki_parse_args={},
                     test=False):

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

        with db_connection(Database, self.logger) as db:
            sql = """DELETE FROM mrt_announcements
                  WHERE prefix != '1.0.0.0/24';"""
            if test:
                db.execute(sql)
            db.vacuum_analyze_checkpoint()

            # Only keep announcements covered by a roa
            # drops old table, unhinges db, performs query, rehinges db
            with db_connection(MRT_W_Roas_Table, self.logger) as mrt_db:
                mrt_db.create_index()
                mrt_db.vacuum_analyze_checkpoint()
                input_table = mrt_db.name

            # Runs the extrapolator and creates the neccessary indexes
            Extrapolator().run_forecast(input_table)

            RPKI_Validator(rpki_args).run_validator(rpki_parse_args)

            db.vacuum_analyze_checkpoint()

            What_If_Analysis(what_if_analysis_args).run_rov_policy()

            db.vacuum_analyze_checkpoint(full=True)
