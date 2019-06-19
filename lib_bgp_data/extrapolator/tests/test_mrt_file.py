#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the MRT_File class"""


import os
import unittest
import logging
import hashlib
from ..logger import Logger
from ..mrt_file import MRT_File

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_MRT_File(unittest.TestCase, Logger):
    """Tests the MRT_File class"""

    # I know we could set up class but this seems more robust
    def setUp(self, url=None):
        """Initializes db and connects"""

        # Up the stream level so we don't get useless info
        args = {"stream_level": logging.ERROR}

        # Args for mrt file
        self.path = "/tmp/bgp_mrt_test"
        self.csv_directory = "/dev/shm/bgp_mrt_test"
        self.url = url
        if self.url is None:
            self.url = ("http://archive.routeviews.org/route-views.nwax/"
                        "bgpdata/2018.12/RIBS/rib.20181229.0000.bz2")
        self.num = 1
        self.total_files = 1

        # MRT_File instance
        self.f = MRT_File(self.path,
                          self.csv_directory,
                          self.url,
                          self.num,
                          self.total_files,
                          self._initialize_logger(args=args),
                          test=True)

    def tearDown(self):
        """Closes db connections"""

        logging.shutdown()
        # destroys all files
        self.f._self_destruct()

    def test_init(self):
        """Tests initialization of an MRT_File through setup"""

        pass

    def test_download_file(self):
        """Tests the download of a file"""

        self.f._download_file()
        # Checks that the file is in the right place
        self.assertTrue(os.path.join(self.path, "1.bz2") == self.f.path)
        # Checks that the file exists and has been downloaded
        self.assertTrue(os.path.exists(self.f.path))

    def test_bz2_unzip(self):
        """Tests unzipping of a bz2 file, default in setUp"""

        self._unzip("1.bz2")

    def test_gz_unzip(self):
        """Tests unzipping of a gz file"""

        self.f.logger.handlers = []
        self.tearDown()
        url = ("http://data.ris.ripe.net/rrc16/2018.12/"
               "bview.20181229.0000.gz")
        self.setUp(url=url)
        self._unzip("1.gz")

    def test_write_csv(self):
        """Tests the writing to a csv file"""

        # NOTE: I know this test is not a good one, however it is impossible
        # to know whether or not the first time this function is run if it is
        # correct, so this is the best I can do for now

        self.f._download_file()
        self.f._unzip_file()
        self.f._write_csv()
        # Checks that the csv file is in the right place
        self.assertTrue(self.f.csv_name == os.path.join(self.csv_directory,
                                                       "1.decompressed.csv"))
        # Checks that the file exists
        self.assertTrue(os.path.exists(self.f.csv_name))
        # Checks that the csv file has stuff in it
        self.assertFalse(self._empty_csv())
        # Check that the csv file is the same
        # this is for ipv6 and ipv4 and no as sets
        file_hash = "9864d23126e3ae53ad5f8c7947e81e98"
        hasher = hashlib.md5()
        with open(self.f.csv_name, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        test_file_hash = hasher.hexdigest()
        self.assertTrue(file_hash == test_file_hash) 

    def itest_bulk_insert_db(self):
        """Tests bulk insertion into the database using a csv"""

        # NOTE: I know this test is not a good one, however it is impossible
        # to know whether or not the first time this function is run if it is
        # correct, so this is the best I can do for now

        self.f._download_file()
        self.f._unzip_file()
        self.f._write_csv()
        # Checks that the database has stuff inserted into the test table
        self.assertTrue(self.f.bulk_insert_db() not in [[], None])

    def itest_parse(self):
        """Tests a full parsing of a file"""

        # NOTE: I know this test is not a good one, however it is impossible
        # to know whether or not the first time this function is run if it is
        # correct, so this is the best I can do for now

        # Checks if parsing a file inserts things into the database
        self.assertTrue(self.f.parse_file(db=True) not in [[], None])

########################
### Helper Functions ###
########################

    def _unzip(self, f_name):
        """Helper function to unzip file"""

        self.f._download_file()
        self.f._unzip_file()
        # Makes sure that old_path is set to the unzipped file
        self.assertTrue(self.f.old_path == os.path.join(self.path, f_name))
        # Checks to make sure that the unzipped file no longer exists
        self.assertFalse(os.path.exists(self.f.old_path))
        # Checks to make sure that the path is set to the decompressed file
        self.assertTrue(self.f.path == os.path.join(self.path,
                                                    "1.decompressed"))
        # Checks to make sure that the new file exists
        self.assertTrue(os.path.exists(self.f.path))

    def _empty_csv(self):
        """Helper function that checks if a csv is empty"""

        with open(self.f.csv_name) as f_csv:
            f_csv.readline()  # skip header
            line = f_csv.readline()
            if line == b'':
                return True
            else:
                return False
