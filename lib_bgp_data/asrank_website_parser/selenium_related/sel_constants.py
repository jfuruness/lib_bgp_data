#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The SeleniumConstants class contains several high use variables that are shared
among the various python files within the selenium_related directory.
"""

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import os


class SeleniumConstants:
    """The SeleniumConstants class contains several high use variables that are shared
    among the various python files within the selenium_related directory.
    """
    FILE_PATH = os.path.dirname(os.path.abspath(__file__))
    CHROMEDRIVER_PATH = os.path.join(FILE_PATH, 'chromedrivers')
    CHROMEDRIVER_NAME = 'chromedriver'
