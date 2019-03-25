#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_File
The MRT File Class allows for the downloading, unzipping, and database
storage of MRT files and data. After each step the unnessecary files are
deleted.
"""

import time
import sys
import csv
import urllib.request
import shutil
import os
import bz2
import gzip
import functools
from ..logger import error_catcher
from .. import utils
from . import mrt_info
from .tables import Announcements_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class MRT_File:
    """File class that allows for download, unzip, and database storage
    The MRT File Class allows for the downloading, unzipping, and database
    storage of MRT files and data. After each step the unnessecary files are
    deleted.
    """

    __slots__ = ['logger', 'name', 'file_name', 'path',
                 'old_path', 'url', 'num', 'total_files', 'csv_dir',
                 'csv_name', 'test', 'ext']

    @error_catcher()
    def __init__(self, path, csv_dir, url, num, total_files, logger):
        """Initializes file instance and determine info about it"""

        self.logger = logger
        self.ext = os.path.splitext(url)[1]
        self.path = "{}/{}{}".format(path, num, self.ext)
        self.url = url
        self.num = num
        self.total_files = total_files
        self.logger.debug("Initialized file instance")
        self.csv_dir = csv_dir

    @error_catcher()
    def __lt__(self, other):
        """less than attribute for sorting files, sorts based on size"""

        # Returns the smallest file size for a comparater
        return os.path.getsize(self.path) < os.path.getsize(other.path)

    @error_catcher()
    def parse_file(self, db, IPV4=True, IPV6=False):
        """Calls all functions to parse a file into the db"""

        self._unzip_file()
        # If db is false, results are printed and not db inserted
        self.csv_name = "{}/{}.csv".format(self.csv_dir,
                                           os.path.basename(self.path))
        utils.write_csv(self.logger,
                        mrt_info.main(self.path, IPV4, IPV6),
                        self.csv_name,
                        files_to_delete=self.path)
        if db:
            utils.csv_to_db(self.logger,
                            Announcements_Table(self.logger),
                            self.csv_name)
        utils.delete_paths(self.logger, [self.path, self.csv_name])


########################
### Helper Functions ###
########################

    @error_catcher()
    def _unzip_file(self):
        """Unzips a file, and deletes the old one"""

        old_path = self.path
        self.path = "{}.decompressed".format(os.path.splitext(self.path)[0])
        args = [self.logger, old_path, self.path]
        utils.unzip_bz2(*args) if self.ext == ".bz2" else utils.unzip_gz(*args)
        utils.delete_paths(self.logger, old_path)
        self.logger.info("Unzipped: {}".format(os.path.basename(self.path)))
