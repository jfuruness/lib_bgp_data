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
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class MRT_File:
    """Converts MRT files to CSVs and then inserts them into a database.
 
    In depth explanation at the top of the file.
    """

    __slots__ = ['logger', 'total_files', 'csv_dir', 'url', 'num', 'ext',
                 'path', 'csv_name']

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
        """less than attribute for sorting files, sorts based on size

        The purpose of this is to be able to sort files in order to be
        able to parse the largest files first"""

        # Returns the smallest file size for a comparater
        return os.path.getsize(self.path) < os.path.getsize(other.path)

    @error_catcher()
    def parse_file(self):
        """Parses a downloaded file and inserts it into the database

        More in depth explanation at the top of the file"""

        # Sets CSV path
        self.csv_name = "{}/{}.csv".format(self.csv_dir,
                                           os.path.basename(self.path))
        # Parses the MRT file into a csv file
        self._bgpdump_to_csv()
        # Inserts the csv file into the Announcements Table
        utils.csv_to_db(self.logger, Announcements_Table, self.csv_name)
        # Deletes all old files
        utils.delete_paths(self.logger, [self.path, self.csv_name])


########################
### Helper Functions ###
########################

    @error_catcher()
    def _bgpdump_to_csv(self):
        """Parses MRT file into a CSV

        This function usesasdfasdf bgpscanner to first be able to read
        the MRT file. This is because BGPScanner is the fastest tool to
        use for this task. Then the sed commands parse the file and
        format the data for a CSV. Then this is stored as a tab
        delimited CSV file, and the original is deleted. For a more in
        depth explanation see top of file. For explanation on specifics
        of the parsing, see below"""

        # I know this may seem unmaintanable, that's because this is a 
        # Fast way to to this. Please, calm down.
        # Turns out not fast - idk if other regexes are faster

        # bgpscanner outputs this format:
        # TYPE|SUBNETS|AS_PATH|NEXT_HOP|ORIGIN|ATOMIC_AGGREGATE|
        # AGGREGATOR|COMMUNITIES|SOURCE|TIMESTAMP|ASN 32 BIT
        # Example: =|1.23.250.0/24|14061 6453 9498 45528 45528|
        # 198.32.160.170|i|||
        # 6453:50 6453:1000 6453:1100 6453:1113 14061:402 14061:2000
        # 14061:2002 14061:4000 14061:4002|198.32.160.170 14061|
        # 1545345848|1


        # performs bgpdump on the file
        bash_args =  'bgpscanner '
        bash_args += self.path
        # Cuts out columns we don't need
        bash_args += ' | cut -d "|" -f1,2,3,10'
        # Now we have TYPE|SUBNETS|AS_PATH|TIMESTAMP
        # Ex: =|1.23.250.0/24|14061 6453 9498 45528 45528|1545345848

        # Makes sure gets announcement, withdrawl, or rib
        # -n for no output if nothing there
        bash_args += ' | sed -n "s/[=|+|-]|'
        # Now we focus on SUBNETS|AS_PATH|TIMESTAMP
        # Ex: 1.23.250.0/24|14061 6453 9498 45528 45528|1545345848
        # Gets three capture groups.
        # The first capture group is the prefix
        # The regex for prefix is done in this way instead of non
        # greedy matching because sed doesn't have non greedy matching
        # so instead the | must be excluded which is slower than this
        bash_args += '\([[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+'
        bash_args += '\.[[:digit:]]\+\/[[:digit:]]\+\)|'
        # Now we focus on AS_PATH|TIMESTAMP
        # Ex: 14061 6453 9498 45528 45528|1545345848
        # Second capture group is as path except for the last number
        bash_args += '\(.*\s\)*'
        # Now we have all but the last number
        # Ex: 45528|1545345848
        # Third capture group is the origin
        bash_args += '\(.*\)'
        # Now we have just the time
        # Example: |1545345848
        # Fourth capture group is the time
        bash_args += '|\(.*\)'
        # Replacement with the capture groups
        bash_args += '/\\1\\t{\\2\\3}\\t\\3\\t\\4/p" | '
        # Replaces spaces in array to commas
        # Need to pipe to new sed because you need the -n -p args
        # to make sed not output the full string if it doesn't match
        # And you cannot add -e args after that
        bash_args += 'sed -e "s/ /, /g" '
        # writes to a csv
        bash_args += '> ' + self.csv_name
        # Subprocess call, waits for completion
        call(bash_args, shell=True)
        self.logger.info("Wrote {}".format(self.csv_name))
        # Deletes old file
        utils.delete_paths(self.logger, self.path)
