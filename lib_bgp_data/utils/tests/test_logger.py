#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the logger.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness", "Nicholas Shpetner"]
__credits__ = ["Justin Furuness", "Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest
import logging
import os
import sys
import io
import contextlib
import warnings
from datetime import datetime
from ..logger import config_logging, _get_log_path


@pytest.mark.logging
class Test_Logging:
    """Tests all local functions within the logger.py file."""

    def test_config_logging(self):
        """Tests the config logging function
        Should log to proper section
        should be able to change the section and have it log properly
        Should log to a file and stdout
        Shouldn't change when you run the func twice
        Should be able to change the default log level
        Should capture warnings
        """
        try:
            from ...database.config import global_section_header
        except ImportError:
            global_section_header = set_global_section_header(section)
        # Make a test logger
        config_logging()
        # Get the path of the log file
        path = _get_log_path(global_section_header)
        # Clear it
        open(path, 'w').close()
        # Prepare to capture stdout
        output = io.StringIO()
        # Try to catch a warning
        with contextlib.redirect_stdout(output):
            logging.warning("Test warning")
        # Check that stdout is not none
        assert output.getvalue() is not None
        # Check file is not none
        with open(path, 'r') as f:
            assert f.read() is not None
            f.close()
        # Clear the file again
        open(path, 'w').close()
        # Set logger to only log warning and worse, and change the section
        config_logging(logging.WARNING, "test")
        # Get the new path
        path = _get_log_path("test")
        # Send info
        logging.info("Test info. You should not see this.")
        # Check to see that it's empty
        with open(path, 'r') as f:
            assert f.read() == ''
            f.close()

    def test_get_log_path(self):
        """Tests get log path func
        Make sure output is what's expected.
        Make sure can create log dir.
        """
        section = "log_test"
        fname = f"{section}_{datetime.now().strftime('%Y_%m_%d')}.log"
        log_path = _get_log_path(section)
        assert os.path.exists("/var/log/lib_bgp_data")
        assert log_path == os.path.join("/var/log/lib_bgp_data", fname)
        return log_path
