#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains all parsers neccessary to parse bgp data

This also contains all the functions to run each individual parser.
The main function of this script, is to run all of these jobs in
the proper order with the proper settings. This can be run as a chron
job"""

from multiprocessing import Process
from .relationships_parser import Relationships_Parser
from .roas_collector import ROAs_Collector
from .bgpstream_website_parser import BGPStream_Website_Parser
from .mrt_parser import MRT_Parser
from .what_if_analysis import What_If_Analysis
from .utils import Pool
from . import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class BGP_Data_Parser:
    """This class contains all the neccessary parsing functions"""

    def __init__(self,
                 start=1553834277,
                 end=1553920677,
                 first_run=False,
                 mrt_parser_args={},
                 relationships_parser_args={},
                 roas_collector_args={},
                 bgpstream_website_parser_args={},
                 What_If_Analysis_args={},
                 rpki_validator_args={}):
        """Initializes vars such as log level etc

        kwargs dictionary includes <name_of_parser>_args"""

        utils.set_common_init_args(self, {}, "bgp data")
        if first_run:
            self.initialize_everything()
        # First we want to parse the mrt files and create the index
        # We can do this in a separate process so that we can run other things
        # This table gets created in ram
        mrt_parser = MRT_Parser(mrt_parser_args)
        mrt_process = Process(target=mrt_parser.parse_files, args=(start, end, ))
        mrt_process.start()
        # While that is going get the relationships data. We aren't going to run this
        # multithreaded because it is so fast, there is no point
        Relationships_Parser(relationships_parser_args).parse_files()
        # While that is running lets get roas, its fast so no multiprocessing
        # This table gets created in RAM
        Roas_Collector(roas_collector_args).parse_roas()
        # We will get the hijack data asynchronously because it will take a while
        website_parser = BGPStream_Website_Parser(
            bgpstream_website_parser_args)
        get_hijacks_process = Process(target=website_parser.parse, args=(start,end,))         
        get_hijacks_process.start()
        # Now we need to wait until the mrt parser finishes it's stuff
        mrt_process.join()
        # Now we are going to join these two tables, and move them out of memory
        with db_connection(Announcements_Covered_By_Roas_Table,
                           self.logger) as db:
            # This function joins mrts and roas which are in ram
            # Then moves the mrts out of ram
            # Then moves the roas out of ram
            # Then splits up the table and deletes unnessecary tables
            db.join_mrt_roas()
            tables = db.get_tables()

        get_hijacks_process.join()
        for table in tables:
            # start extrapolator
            # run the rpki validator concurrently
            rpki_parser = RPKI_Validator(rpki_validator_args)
            rpki_process = Process(target=rpki_parser.run_validator, args=(table, ))
            rpki_process.start()
            self.run_extrapolator()
            rpki_process.join()
            wia = What_If_Analysis(what_if_analysis_args)
            wia.run_policies()
            with db_connection(Database, self.logger) as db:
                db.cursor.execute("DROP TABLE {}".format(table))
                db.cursor.execute("DROP TABLE extrapolation_results;")
        with db_connection(Database, self.logger) as db:
            # CLEAN OUT DATABASE HERE!!!!!!!!
            db.cursor.execute("VACUUM FULL;")


    def initialize_everything(self):
        """Runs the data collection for all data within a period of time"""

        pass##############################TODO

        # Run initial setup - setup database
        # Connect to database, make some tables, drop everything that is in there
        # Optimize database for performance
        # install all dependencies using pyenv and activate
        # parse relationships, bgpstream website, roas, mrt_files, index, vaccuum, extrapolator
        # delete unnessecary tables, vaccuum again

if __name__ == "__main__":
    bgp_data_parser()
