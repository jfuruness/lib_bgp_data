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
from .relationships_file import AS_2_File
from ..logger import Logger, error_catcher
from .tables import Customer_Providers_Table, Peers_Table
from ..config import Config
from .. import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Relationships_Parser:
    """This class downloads, unzips, parses, and deletes files from Caida"""

    __slots__ = ['path', 'csv_dir', 'args', 'url', 'logger', 'config',
                 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # URLs fom the caida websites to pull data from
        self.url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        # Sets args such as path, csv_dir, logger, config, etc
        utils.set_common_init_args(self, args, "Relationship")

    # Note that the utils.run_parser decorator deletes/creates all paths,
    # records start/end time, and upon end or error deletes everything
    @error_catcher()
    @utils.run_parser()
    def parse_files(self, db=True):
        """Downloads, unzips, and parses file"""

        url, int_date = self._get_url()
        # If this is a new file, the config date will be less than the
        # websites file date, and so we renew our data
        if self.config.last_date < int_date:
            AS_2_File(self.logger, self.path, self.csv_dir, url
                ).parse_file(db)
            self.config.update_last_date(int_date)
        else:
            self.logger.info("old file, not parsing")

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_url(self):
        """Gets urls to download relationship files"""

        # Get all html tags that might have links
        elements = [x for x in utils.get_tags(self.url, 'a')[0]]
        # Gets the last file of all bz2 files
        url = [x["href"] for x in elements if "bz2" in x["href"]][-1]
        # Returns the url and the date for the url
        return url, max(map(int, re.findall('\d+', url)))
