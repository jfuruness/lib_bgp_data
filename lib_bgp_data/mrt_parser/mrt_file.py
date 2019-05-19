#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_File.

The MRT_File class contains the functionality to nload and parse
mrt files. This is done through a series of steps

1. Initialize the MRT_File class
2. The MRT File will be downloaded from the MRT_Parser using utils
3. Parse the MRT_File using bgpscanner and sed
    -bgpscanner is used because it is the fastest BG{ dump scanner
    -sed is used because it is cross compatable and fast
        -Must use regex parser that can find/replace for array format
    -Possible future extensions:
        -Use a faster regex parser?
        -Add parsing updates functionality?
3. Parse the MRT_File into a CSV
    -Handled in _bgpdump_to_csv function
    -This is done because there are 30-100GB of data
    -Fast insertion is needed, bulk insertion is the fastest
        -CSV is fastest insertion method, second only to binary
        -Binary insertion isn't cross compatable with postgres versions
    -Delete old files
4. Insert the CSV file into the database using COPY and then deleted
    -Handled in parse_file function
    -Unnessecary files deleted for space

Design choices (summarizing from above):
    -bgpscanner is the fastest BGP dump scanner so it is used to parse
    -sed is used for regex parsing because it is fast and portable
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files

Possible Future Extensions:
    -Add functionality to download and parse updates?
    -Test different regex parsers other than sed for speed?
"""

import time
import sys
import csv
import urllib.request
import shutil
import os
import functools
from subprocess import call
from ..utils import utils, error_catcher
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
    def parse_file(self):
        """Calls all functions to parse a file into the db"""

        # If db is false, results are printed and not db inserted
        self.csv_name = "{}/{}.csv".format(self.csv_dir,
                                           os.path.basename(self.path))
        self._bgpdump_to_csv()
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
        # Turns out not fast - idk if other regexes are faster

        # performs bgpdump on the file
        1/0 # break so i don't forget need to make bgpscanner and test with backslashes
        bash_args =  'bgpscanner '
        bash_args += self.path
        # Cuts out columns we don't need
        bash_args += ' | cut -d "|" -f1,3,10,11'
        # Makes sure gets announcement, withdrawl, or rib
        # -n for no output if nothing there
        bash_args += ' | sed -n "s/[=|+|-]|'
        # Gets three capture groups.
        # First capture group is as path
        # Second capture group is as path up to origin
        bash_args += '\(\([^{]*\s\)*'
        # Third capture group is the origin
        bash_args += '\([[:digit:]]\+\)\)'
        # Fourth capture group is the time
        bash_args += '|\(.*\)'
        # Fifth capture group is the origin
        bash_args += '|\(.*\)'
        # Replacement with the capture groups
        bash_args += '/{\\1}\\t\\3\\t\\4\\t\\5/p" '
        # writes to a csv
        1/0####NEED TO CAHNGE SPACES TO COMMAS!!!
        bash_args += '> ' + self.csv_name
        call(bash_args, shell=True)
        self.logger.info("Wrote {}".format(self.csv_name))
        utils.delete_paths(self.logger, self.path)
