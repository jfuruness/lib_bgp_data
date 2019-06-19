#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the Logger class"""


import os
import unittest
import logging
import shutil
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from ..logger import Logger

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class TestLogger(unittest.TestCase, Logger):
    """Tests the config class"""

    def test_print_stream(self):
        """Tests initialization of print stream"""

        self.logger = self._initialize_logger()
        # Creates a new input output stream for the logger
        log_out = StringIO()
        # Sets the loggers stream to the new IO stream
        self.stream_handler.stream = log_out
        # log a critical message so it should get logged
        self.logger.critical("hello")
        # Get the message that was logged
        output = log_out.getvalue().strip()
        self.assertTrue('hello' in output)
        # Must end logging instance before running other tests
        logging.shutdown()

    def test_print_stream_levels(self):
        """Tests that only certain logging levels are printed"""

        self.logger = self._initialize_logger()
        # Captures output
        log_out = self._change_stream()

        # log a critical message so it should get logged
        self.logger.critical("hello")
        # Get the message that was logged
        output = log_out.getvalue().strip()
        self.assertTrue('hello' in output)

        # log a debug message so that it shouldn't get logged
        self.logger.debug("wrong")
        # Get the message that was logged
        output = log_out.getvalue().strip()
        self.assertFalse('wrong' in output)

        # Must end logging instance before running other tests
        logging.shutdown()

        # Change the level to which logger is initialized
        args = {"stream_level": logging.WARNING}
        self.logger = self._initialize_logger(args=args)
        # Creates a new input output stream for the logger
        log_out = self._change_stream()

        # log a info message so that it shouldn't get logged
        self.logger.debug("wrong")
        # Get the message that was logged
        output = log_out.getvalue().strip()
        self.assertFalse('wrong' in output)
        
        # log a critical message so it should get logged
        self.logger.critical("correct")
        # Get the message that was logged
        output = log_out.getvalue().strip()
        self.assertTrue('correct' in output)
        logging.shutdown()

    def _change_stream(self):
        """Helper function to change output of stream_handler"""

        # Creates a new input output stream for the logger
        log_out = StringIO()
        # Changes the output stream to log_out
        self.stream_handler.stream = log_out
        return log_out

    def test_file_handler(self):
        """Tests initialization of file handler"""

        # Initialize logger in a test directory
        args = {"stream_level": logging.CRITICAL,
                "log_dir": "/var/log/bgp_mrt_test"}
        self.logger = self._initialize_logger(args=args)
        log_me = "hello"
        self.logger.error(log_me)
        self.assertTrue(log_me in self._read_file())
        logging.shutdown()
        self.assertTrue(os.path.exists(self.file_path))
        # Had to comment this line out because of the server permissions
        # shutil.rmtree(args.get("log_dir"))

    def test_file_handler_levels(self):
        """Tests file handler levels"""

        # Initialize logger in a test directory
        args = {"stream_level": logging.CRITICAL,
                "log_dir": "/var/log/bgp_mrt_test"}
        self.logger = self._initialize_logger(args=args)

        # Checks that equal logging level items in file
        log_me = "correct"
        self.logger.warning(log_me)
        self.assertTrue(log_me in self._read_file())

        # Checks that lesser logging levels are not in file
        log_me = "wrong"
        self.logger.info(log_me)
        self.assertFalse(log_me in self._read_file())

        logging.shutdown()

        # Initialize logger in a test directory
        args = {"stream_level": logging.CRITICAL,
                "file_level": logging.ERROR,
                "log_dir": "/var/log/bgp_mrt_test"}
        self.logger = self._initialize_logger(args=args)
        self.assertTrue(os.path.exists(self.file_path))

        # Checks that equal logging level items in file
        log_me = "correct"
        self.logger.error(log_me)
        self.assertTrue(log_me in self._read_file())

        # Checks that lesser logging levels are not in file
        log_me = "wrong"
        self.logger.warning(log_me)
        self.assertFalse(log_me in self._read_file())

        # Shutdown logging instance and remove the directory
        logging.shutdown()
        # Had to comment this line out because of server permissions
        # shutil.rmtree(args.get("log_dir"))


    def _read_file(self):
        """Reads a file and closes it"""

        f = open(self.file_path, mode='r')
        lines = f.read()
        f.close()

