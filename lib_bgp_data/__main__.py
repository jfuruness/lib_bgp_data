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
from .relationships_parser import Relationships_Parser
from .roas_collector import ROAs_Collector
from .bgpstream_website_parser import BGPStream_Website_Parser
from .mrt_parser import MRT_Parser
from .what_if_analysis import What_If_Analysis, RPKI_Validator
from .utils import utils, Database, db_connection
from .utils import Announcements_Covered_By_Roas_Table, Stubs_Table

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
                 start=1555286400,
                 end=1555372800,
                 first_run=False,
                 mrt_parser_args={},
                 relationships_parser_args={},
                 roas_collector_args={},
                 bgpstream_website_parser_args={},
                 what_if_analysis_args={},
                 rpki_validator_args={}):
        """Initializes vars such as log level etc

        kwargs dictionary includes <name_of_parser>_args"""

        utils.set_common_init_args(self, {}, "bgp data")
        self.logger.info("starting data parser")

        if first_run:
            self.initialize_everything()
        # First we want to parse the mrt files and create the index
        # We can do this in a separate process so that we can run other things
        # This table gets created in ram
#        mrt_parser = MRT_Parser(mrt_parser_args)#################################
#        mrt_process = Process(target=mrt_parser.parse_files, args=(start, end, ))#################
#        mrt_process.start()############################################
        # While that is going get the relationships data. We aren't going to run this
        # multithreaded because it is so fast, there is no point
#        Relationships_Parser(relationships_parser_args).parse_files()############################
        # While that is running lets get roas, its fast so no multiprocessing
        # This table gets created in RAM
#        ROAs_Collector(roas_collector_args).parse_roas()#############################
#        input("EXIT")
        # We will get the hijack data asynchronously because it will take a while
#        website_parser = BGPStream_Website_Parser(########################
#            bgpstream_website_parser_args)#############################
#        get_hijacks_process = Process(target=website_parser.parse, args=(start,end,))##########    
#        get_hijacks_process.start()##########################
        # Now we need to wait until the mrt parser finishes it's stuff
#        mrt_process.join()############################################
        # Now we are going to join these two tables, and move them out of memory
        with db_connection(Announcements_Covered_By_Roas_Table,
                           self.logger) as db:
            # This function joins mrts and roas which are in ram
            # Then moves the mrts out of ram
            # Then moves the roas out of ram
            # Then splits up the table and deletes unnessecary tables
#            self.logger.info("analyzing now")
#            db.cursor.execute("VACUUM ANALYZE")
#            self.logger.info("dine analys")
#            self.logger.info("kjoining")
#            db.join_mrt_with_roas()
#            self.logger.info("done joining")
            tables = db.get_tables()
#########            db.cursor.execute("DROP TABLE IF EXISTS extrapolation_inverse_results;")
#            db.cursor.execute("SET enable_seqscan TO TRUE;")
#            db.cursor.execute("CHECKPOINT;")
#            db.cursor.execute("VACUUM ANALYZE;")

#        get_hijacks_process.join()########################
#        input("start rpki")
        rpki_parser = RPKI_Validator(rpki_validator_args)
        rpki_process = Process(target=rpki_parser.run_validator)        
        rpki_process.start()
        rpki_process.join()#########################################

        input("start extrapolator")


        with db_connection(Database, self.logger) as db:
            for table in tables:
                # start extrapolator
                # run the rpki validator concurrently
                extrap_args = "/home/ubuntu/bgp-extrapolator -a {}".format(table)
                Popen([extrap_args], shell=True).wait()
                print("table is {}".format(table))
#                db.cursor.execute("DROP TABLE {}".format(table))
                db.cursor.execute("CHECKPOINT;")
        create_exr_index_sqls = ["""CREATE INDEX ON 
            extrapolation_inverse_results USING GIST(prefix inet_ops);""",
            """CREATE INDEX ON extrapolation_inverse_results
                USING GIST(prefix inet_ops, origin);"""]        
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

if __name__ == "__main__":
    bgp_data_parser()
