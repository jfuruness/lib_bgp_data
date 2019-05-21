#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationships_Parser which can parse an AS Graph

AS_2 Files are the only ones used now since they are the most accurate
NOTE: Upon initialization database clears old entries, so only new entries
are created
"""

import re
import requests
import shutil
import os
import bs4
import datetime
from datetime import timedelta
import multiprocessing
from pathos.multiprocessing import ProcessingPool as Pool
from .relationships_file import Rel_File
from .tables import Customer_Providers_Table, Peers_Table
from ..utils import utils, Config, db_connection
from ..utils import Thread_Safe_Logger as Logger, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Relationships_Parser:
    """This class downloads, unzips, parses, and deletes files from Caida"""

    __slots__ = ['path', 'csv_dir', 'logger']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets args such as path, csv_dir, logger, config, etc
        utils.set_common_init_args(self, args, "Relationship")

    # Note that the utils.run_parser decorator deletes/creates all paths,
    # records start/end time, and upon end or error deletes everything
    @error_catcher()
    @utils.run_parser()
    def parse_files(self):
        """Downloads, unzips, and parses file"""

        url, int_date = self._get_url()
        # If this is a new file, the config date will be less than the
        # websites file date, and so we renew our data
        config = Config(self.logger)
        if config.last_date < int_date:
            Rel_File(self.path, self.csv_dir, url, self.logger).parse_file()
            config.update_last_date(int_date)
        else:
            self.logger.info("old file, not parsing")

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_url(self):
        """Gets urls to download relationship files"""

        url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        # Get all html tags that might have links
        elements = [x for x in utils.get_tags(url, 'a')[0]]
        # Gets the last file of all bz2 files
        file_url = [x["href"] for x in elements if "bz2" in x["href"]][-1]
        return file_url, int_date
