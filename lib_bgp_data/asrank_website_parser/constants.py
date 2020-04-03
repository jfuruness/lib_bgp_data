#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The Constants class contains several high use enums that are shared
among the various python files within the asrank_website_parser
directory.
"""

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from enum import Enum
import os


class Constants(Enum):
    """The Constants class contains several high use enums that are shared
    among the various python files within the asrank_website_parser
    directory.
    """
    FILE_PATH = os.path.dirname(os.path.abspath(__file__))
    CSV_FILE_NAME = 'asrank_caida.csv'

    URL = 'https://asrank.caida.org/'
    ENTRIES_PER_PAGE = 1000

    NUM_THREADS = 20
    RETRIES = 3
