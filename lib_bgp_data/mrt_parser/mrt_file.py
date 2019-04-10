#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_File
The MRT File Class allows for the downloading, unzipping, and database
storage of MRT files and data. After each step the unnessecary files
are deleted.
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
from subprocess import call
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
        self.total_files = total_files
        self.csv_dir = csv_dir
        self.url = url
        self.num = num
        self.ext = os.path.splitext(url)[1]
        self.path = "{}/{}{}".format(path, num, self.ext)
        self.logger.debug("Initialized file instance")

    @error_catcher()
    def __lt__(self, other):
        """less than attribute for sorting files, sorts based on size"""

        # Returns the smallest file size for a comparater
        return os.path.getsize(self.path) < os.path.getsize(other.path)

    @error_catcher()
    def parse_file(self, db):
        """Calls all functions to parse a file into the db"""

        # If db is false, results are printed and not db inserted
        self.csv_name = "{}/{}.csv".format(self.csv_dir,
                                           os.path.basename(self.path))
        self._bgpdump_to_csv()
        if db:
            utils.csv_to_db(self.logger, Announcements_Table, self.csv_name)
        utils.delete_paths(self.logger, [self.path, self.csv_name])


########################
### Helper Functions ###
########################

    @error_catcher()
    def _bgpdump_to_csv(self):
        """Function takes mrt file and converts it to a csv with bash"""

        # I know this may seem unmaintanable, that's because this is a 
        # Fast way to to this. Please, calm down.

        # performs bgpdump on the file
        bash_args =  'bgpdump -q -M -t change '
        bash_args += self.path
        # Cuts out columns we don't need
        bash_args += ' | cut -d "|" -f2,6,7 '
        # Deletes any announcements with as sets
        bash_args += '|sed -e "/{.*}/d" '
        # Performs regex matching with sed and adds brackets around the as_path
        bash_args += '-e "s/\(.*|.*|\)\(.*$\)/\\1{\\2}/g" '
        # Replaces pipes and spaces with commas for csv insertion
        # leaves out first one
        bash_args += '-e "s/ /, /g" -e "s/, / /" -e "s/|/\t/g" '
        # Adds a column for the origin
        bash_args += '-e "s/\([[:digit:]]\+\)}/\\1}\t\\1/g"'
        # writes to a csv
        bash_args += '> ' + self.csv_name
        call(bash_args, shell=True)
        self.logger.info("Wrote {}".format(self.csv_name))
        utils.delete_paths(self.logger, self.path)
