#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the config class"""


import os
import unittest
import logging
from ..logger import Logger
from ..config import Config

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class TestConfig(unittest.TestCase, Logger):
    """Tests the config class"""

    def setUp(self):
        """Sets up logging with higher logging level"""
        args = {"stream_level": logging.ERROR}
        self.logger = self._initialize_logger(args=args)

    def tearDown(self):
        """Ends logging"""

        logging.shutdown()

    def test_file_exists(self, config=None):
        """Tests that the config file exists"""

        if config is None:
            config = Config(self.logger)
        self.assertTrue(os.path.exists(config.path))

    def test_sections_exist(self, config=None):
        """Tests that the sections in the config file exist"""

        if config is None:
            config = Config(self.logger)
        args = Config(self.logger).get_db_creds()
        self.assertTrue(None not in args)

    def test_reading_correctly(self):
        """Tests that a fake config file is read correctly"""

        try:
            config = Config(self.logger, path="/tmp/bgp_temp_test.conf")
            # Creates config file
            f = open("/tmp/bgp_temp_test.conf", "w+")
            sections = ["user", "password", "host", "database"]
            correct_vals = {sections[i]: str(i) for i in range(len(sections))}
            f.write("[bgp]\n")
            for key, val in correct_vals.items():
                f.write("{}: {}\n".format(key, val))
            f.close()
            # Checks that the path exists for the new config file
            self.test_file_exists(config)
            # Checks that the sections exists in the file we've created
            self.test_sections_exist(config)
            # Checks that the sections are read correctly
            self.assertTrue(config.get_db_creds() == correct_vals)
        except Exception as e:
            raise e
        finally:
            # Makes sure to always remove the files
            os.remove("/tmp/bgp_temp_test.conf")
