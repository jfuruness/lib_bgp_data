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

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class bgp_data_parser:
    """This class contains all the neccessary parsing functions"""

    def __init__(self, **kwargs):
        """Initializes vars such as log level etc

        kwargs dictionary includes <name_of_parser>_args"""

        self.__dict__.update(kwargs)

        pass########################TODO

    def parse_relationships(self, db=True):
        """Parses relationship data into database"""

        pass###############TODO

    def parse_bgpstream_website(self, db=True, row_limit=None):
        """Parses bgpstream.com data into database"""

        pass###########################TODO

    def parse_roas(self, db=True):
        """Parses roas into the database"""

        pass#########################TODO

    def parse_mrt_files(self,
                        start,
                        end,
                        download_threads,
                        parse_threads,
                        db=True
                        IPV4=True,
                        IPV6=False):

        """Parses mrt files into the database"""

    def extrapolate(self):
        """Runs bgpextrapolator, propogates announcements into db"""

        pass#################################TODO

    def collect_data(self,
                     start,
                     end,
                     download_threads,
                     parse_threads,
                     db=True,
                     IPV4=True,
                     IPV6=False,
                     row_limit=None)
        """Runs the data collection for all data within a period of time"""

        pass##############################TODO

        # Run initial setup - setup database
        # Connect to database, make some tables
        # Optimize database for performance
        # install all dependencies using pyenv and activate
        # parse relationships, bgpstream website, roas, mrt_files, index, vaccuum, extrapolator
        # delete unnessecary tables, vaccuum again
