#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains all parsers neccessary to parse bgp data

This also contains all the functions to run each individual parser.
The main function of this script, is to run all of these jobs in
the proper order with the proper settings. This can be run as a chron
job"""

from .relationships_parser import Relationships_Parser
from .roas_collector import ROAs_Collector
from .bgpstream_website_parser import BGPStream_Website_Parser
from .mrt_parser import MRT_Parser
from .what_if_analysis import What_If_Analysis
from .mrt_parser import Pool

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class bgp_data_parser:
    """This class contains all the neccessary parsing functions"""

    def __init__(self,
                 start=1553834277,
                 end=1553920677,
                 first_run=False,
                 mrt_parser_args={},
                 mrt_parse_args=[],
                 relationships_parser_args={},
                 relationship_parse_args=[]
                 roas_collector_args={},
                 roas_collector_parse_args=[],
                 bgpstream_website_parser_args={},
                 bgpstream_website_parse_args=[], 
                 What_If_Analysis_args={},
                 what_if_analysis_parse_args=[],
                 rpki_validator_args={}):
        """Initializes vars such as log level etc

        kwargs dictionary includes <name_of_parser>_args"""

        utils.set_common_init_args(self, args, "bgp data")
        if first_run:
            self.initialize_everything()
        # First we want to parse the mrt files. This will take up all
        # threads and saturates the io, so we do this non multithreaded
        mrt_parser = MRT_Parser(mrt_parser_args)
        mrt_parser.parse_files(start, end)
        
        # After this we need an index on the prefix for this table for
        # The extrapolator. We can run this in it's own process
        # asynchronously for now
        mrt_index_process = Process(target=mrt_parser.create_index)
        mrt_index_process.start()
        # While that index is being created, lets get the hijack data
        website_parser = BGPStream_Website_Parser(
            bgpstream_website_parser_args)
        get_hijacks_process = Process(target=website_parser.parse, args=(start,end,))         
        get_hijacks_process.start()
        # While we are getting the hijack data, lets get the roas too
        roas_collector = Roas_Collector(roas_collector_args)
        get_roas_process = Process(target=roas_collector.parse_roas)
        get_roas_process.start()
        # While that process is running, lets get the relationship data
        rel_parser = Relationships_Parser(relationships_parser_args)
        get_relationships_process = Process(target=rel_parser.parse_files)
        get_relationships_process.start()

        # At the same time as all of that is running/completing,
        # We can start ripe
        rpki_parser = RPKI_Validator(rpki_validator_args)
        rpki_process = Process(target=rpki_process.run_validator)
        rpki_process.start()

        # The roas should have completed now, so join that process
        get_roas_process.join()
        # Hopefully our index will be done by now, so join that process
        mrt_index_process.join()
        #######
        # join the mrt and roas table, and create index in same thread, make a main_tables.py file in this directory
        # while the tables are joining, 
        #   join hijack and validity things, create all validity intersect hijack tables, and create indexes
        # join the relationships process
        # join the mrt intersect roas process
        # start extrapolator here
        # join the hijack and validity process
        # join the extrapolator process
        # Get the announcement thing
        # run the what if analysis, get announcement thing last (add column at the end)

    def initialize_everything(self)
        """Runs the data collection for all data within a period of time"""

        pass##############################TODO

        # Run initial setup - setup database
        # Connect to database, make some tables
        # Optimize database for performance
        # install all dependencies using pyenv and activate
        # parse relationships, bgpstream website, roas, mrt_files, index, vaccuum, extrapolator
        # delete unnessecary tables, vaccuum again
