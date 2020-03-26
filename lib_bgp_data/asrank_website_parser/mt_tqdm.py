#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains an abstraction of a Selenium Chrome webdriver

The purpose of this class is to simplify the use of
chromedriver by abstracting the various functions
and initialization into an easy-to-use class/ context manager.

1. Initialize the class
    -Handled in the __init__ function
    -Sets the table and the csv_path, and then calls __init__ on Data
2. Call __init__ on the parent class Data.
    -This initializes all regexes
    -The data list of all events of that type is also initialized
3. Rows are appended to each data class
    -This is handled by the BGPStream_Website_Parser class
    -The append function is overwritten in the parent Data class
4. For each row, parse the common elements
    -Handled by the append _parse_common_elements in the Data class
    -Gets all information that is generic to all events
5. Pass extra information to the _parse_uncommon_elements function
    -This is a function specified by each subclass
    -This function parses elements that are specific to that event type
6. Then the row is formatted for csv insertion and appended to self.data
    -Formatting is handled by the _format_temp_row() in the Data Class
7. Later the BGPStream_Website_Parser will call the db_insert function
    -This is handled in the parent Data class
    -This will insert all rows into a CSV
        -This is done because CSVs have fast bulk insertion time
    -The CSV will then be copied into the database
8. After the data is in the database, the tables will be formatted
    -First the tables remove unwanted IPV4 and IPV6 values
    -Then an index is created if it doesn't exist
    -Then duplicates are deleted if they exist
    -Then temporary tables are created
        -These are tables that are subsets of the overall data

Design Choices (summarizing from above):
    -This is a mess, parsing this website is messy so I will leave it
    -Parsing is done from the last element to the first element
        -This is done because not all pages start the same way

Possible Future Extensions:
    -Add test cases
"""


__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from threading import Lock
from tqdm import tqdm
import os

from .constants import Constants


class MtTqdm:
    """Implement a tqdm progress bar that
    supports multithreaded manual updating
    """

    def __init__(self, update_value):
        self._lock = Lock()
        self._pbar = tqdm(total=100)
        self._update_val = update_value

    def update(self):
        """Update the tqdm progress bar. Thread safe"""
        self._lock.acquire()
        if (self._pbar.n + self._update_val) >= self._pbar.total:
            self._pbar.update(self._pbar.total - self._pbar.n)
        else:
            self._pbar.update(self._update_val)
        self._lock.release()

    def close(self):
        """Close the tqdm progress bar"""
        if self._pbar.n < self._pbar.total:
            self._pbar.update(self._pbar.total - self._pbar.n)
        self._pbar.close()
