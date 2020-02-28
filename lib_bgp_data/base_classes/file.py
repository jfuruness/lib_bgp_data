#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class File.

This is the base class for MRT_File and Relationship_File.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
from .decometa import DecoMeta
from ..utils import Thread_Safe_Logger as Logger


class File:
    """Converts MRT files to CSVs and then inserts them into a database.

    In depth explanation in README.
    """

    __slots__ = ['logger', 'csv_dir', 'url', 'num', 'path', 'csv_name']

    __metaclass__ = DecoMeta

    def __init__(self,
                 path: str,
                 csv_dir: str,
                 url: str,
                 num: int = 1,
                 logger=Logger()):
        """Initializes file instance and determine info about it"""

        self.logger = logger
        self.csv_dir = csv_dir
        self.url = url
        self.num = num
        self.path = f"{path}/{num}{os.path.splitext(url)[1]}"
        self.logger.debug("Initialized file instance")

    def __lt__(self, other):
        """less than attribute for sorting files, sorts based on size

        The purpose of this is to be able to sort files in order to be
        able to parse the largest files first
        """

        if isinstance(other, File):
            # Returns the smallest file size for a comparater
            return os.path.getsize(self.path) < os.path.getsize(other.path)
