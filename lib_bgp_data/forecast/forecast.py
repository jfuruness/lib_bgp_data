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
from ..what_if_analysis import What_If_Analysis, RPKI_Validator
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
    def __init__(self,
                 start=utils.get_default_start(),
                 end=utils.get_default_end(),
                 filter_by_roas=True,
                 fresh_install=False,
                 forecast_args={},
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
                 rpki_parse_args={}):
        """Initializes vars such as log level etc

        kwargs dictionary includes <name_of_parser>_args"""

        utils.set_common_init_args(self, forecast_args)
        self.logger.info("starting Forecast")

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
        if filter_by_roas:
            # Only keep announcements covered by a roa
            # drops old table, unhinges db, performs query, rehinges db
            with db_connection(MRT_W_Roas_Table, self.logger) as db:
                db.create_index()
                self.logger.info("analyzing now")
                db.execute("VACUUM ANALYZE")
        input_table = "mrt_w_roas" if filter_by_roas else None
        Extrapolator().run_forecast(input_table)
        return
        create_exr_index_sqls = ["""CREATE INDEX ON 
            extrapolation_inverse_results USING GIST(prefix inet_ops);""",
            """CREATE INDEX ON extrapolation_inverse_results
                USING GIST(prefix inet_ops, origin);"""]


        input("!!!!!!!!!!!!!!!!!!!!!!!!!!")
        RPKI_Validator(rpki_args).run_validator(rpki_parse_args)
        input("ABOUT TO PERFORM Multiproc exec")
        input("PRESS ONE MORE TIME")
        # Generates the final stubs table, and creates indexes
        with db_connection(Database, self.logger) as db:
            db.multiprocess_execute(create_exr_index_sqls)
        with db_connection(Stubs_Table, self.logger) as db:
            db.generate_stubs_table()
            db.cursor.execute("VACUUM FULL ANALYZE;")


            db.cursor.execute("CHECKPOINT;")

        rpki_process.join()#############################     
#        rpki_process.join()#######################
        input("rpki done running")
        wia = What_If_Analysis(what_if_analysis_args)
        wia.run_policies()
        with db_connection(Database, self.logger) as db:
            # CLEAN OUT DATABASE HERE!!!!!!!!
            db.cursor.execute("VACUUM FULL ANALYZE;")


            db.cursor.execute("CHECKPOINT;")



    def initialize_everything(self):
        """Runs the data collection for all data within a period of time"""

        pass##############################TODO

        # Run initial setup - setup database
        # Connect to database, make some tables, drop everything that is in there
        # Optimize database for performance
        # install all dependencies using pyenv and activate
        # parse relationships, bgpstream website, roas, mrt_files, index, vaccuum, extrapolator
        # delete unnessecary tables, vaccuum again
