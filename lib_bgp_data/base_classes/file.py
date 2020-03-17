#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class File.

This is the base class for MRT_File and Relationship_File.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging
import os


class File:
    """Converts files to CSVs and then inserts them into a database.

    In depth explanation in README.
    """

    __slots__ = ['csv_dir', 'url', 'num', 'path', 'csv_name']

    def __init__(self,
                 path: str,
                 csv_dir: str,
                 url: str,
                 num: int = 1):
        """Initializes file instance and determine info about it"""

        self.csv_dir = csv_dir
        self.url = url
        self.num = num
        # Creates path as path/num/extension
        self.path = f"{path}/{num}{os.path.splitext(url)[1]}"
        logging.debug("Initialized file instance")

    def __lt__(self, other) -> bool:
        """less than attribute for sorting files, sorts based on size

        The purpose of this is to be able to sort files in order to be
        able to parse the largest files first
        """

        if isinstance(other, File):
            # Returns the smallest file size for a comparater
            return os.path.getsize(self.path) < os.path.getsize(other.path)
