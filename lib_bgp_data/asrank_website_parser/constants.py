#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The Constants class contains several high use variables that are shared
among the various python files within the asrank_website_parser
directory.
"""

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import os


class Constants:
    """The Constants class contains several high use variables that are shared
    among the various python files within the asrank_website_parser
    directory.
    """
    FILE_PATH = os.path.dirname(os.path.abspath(__file__))
    CHROMEDRIVER_NAME = 'chromedriver'
    CHROMEDRIVER_PATH = os.path.join(os.path.join(FILE_PATH,
                                                  'selenium_related'),
                                     'chromedrivers')

    URL = 'https://asrank.caida.org/'
    CSV_FILE_NAME = 'asrank_caida.csv'
    ENTRIES_PER_PAGE = 1000
    NUM_THREADS = 11
