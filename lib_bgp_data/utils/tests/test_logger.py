#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the logger.py file.

For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..logger import config_logging, _get_log_path

@pytest.mark.logging
class Test_Logging:
    """Tests all local functions within the logger.py file."""

    @pytest.mark.skip(reason="new hires work")
    def test_config_logging(self):
        """Tests the config logging function

        Should log to proper section
        should be able to change the section and have it log properly
        Should log to a file and stdout
        Shouldn't change when you run the func twice
        Should be able to change the default log level
        Should capture warnings
        """

        pass

    @pytest.mark.skip(reason="New hires work")
    def test_get_log_path(self):
        """Tests get log path func

        Make sure output is what's expected.
        Make sure can create log dir.
        """

        pass
