#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains all of the data classes for parsing

The purpose of these classes is to parse information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. Please note that each data class inherits from the
Data class. For each data class, This is done through a series of steps.

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
    -A parent data class is used because many functions are the same
     for all data types
    -This is a mess, parsing this website is messy so I will leave it
    -Parsing is done from the last element to the first element
        -This is done because not all pages start the same way

Possible Future Extensions:
    -Add test cases
    -Ask bgpstream.com for an api?
        -It would cause less querying of their site
"""


#from ..utils import utils, error_catcher, db_connection
#from .tables import Hijack_Table, Outage_Table, Leak_Table

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import csv
import os

from .constants import Constants


class ASRankData:
    """Class where the parsed rows of asrank.caida.org 
    are saved. 

    For a more in depth explanation see the top of the file.
    """

    #__slots__ = ['logger']

    #@error_catcher()
    #def __init__(self, logger, total_entries):
    def __init__(self, total_entries):
        #self.logger = logger
        #self.logger.debug("Initialized row")
        
        self._as_rank = None
        self._as_num = None
        self._org = None
        self._country = None
        self._cone_size = None
        
        self._elements_lst = None
        self._total_entries = total_entries
        self._init()

    def _init(self):
        """Initialize the five columns of information found on asrank.caida.org"""
        self._as_rank = [0] * self._total_entries
        self._as_num = [0] * self._total_entries
        self._org = [0] * self._total_entries
        self._country = [0] * self._total_entries
        self._cone_size = [0] * self._total_entries

        self._elements_lst = [self._as_rank,
                              self._as_num,
                              self._org,
                              self._country,
                              self._cone_size] 

    def insert_data(self, page_num, tds_lst):
        """Given a list of HTML table cells (tds), insert into the respective
        element list."""
        for i in range(0, len(tds_lst) // len(self._elements_lst)):
            for j, element in enumerate(self._elements_lst):
                temp_ind = i * len(self._elements_lst) + j
                el_ind = page_num * Constants.ENTRIES_PER_PAGE + i

                if j != 3:
                    if j == 2 and len(tds_lst[temp_ind].text) == 0:
                        element[el_ind] = 'unknown'
                    else:
                        element[el_ind] = tds_lst[temp_ind].text
                else:
                    element[el_ind] = str(tds_lst[temp_ind])[-16:-14]

    def write_csv(self, csv_path):
        """Convert the stored data into a tab separated csv file at path, csv_path"""
        with open(os.path.join(Constants.FILE_PATH, csv_path), mode='w') as temp_csv:
            csv_writer = csv.writer(temp_csv, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for i in range(len(self._as_rank)):
                row = [lst[i] for lst in self._elements_lst]
                csv_writer.writerow(row)

    def get_elements_lst(self):
        return self._elements_lst
