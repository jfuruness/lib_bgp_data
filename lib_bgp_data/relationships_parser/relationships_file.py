#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationship_File

The MRT File Class allows for the downloading, unzipping, and database
storage of MRT files and data. After each step the unnessecary files are
deleted.

The other classes are for specific types of files and include how to parse
those particular files
"""

from enum import Enum
import re
import os
from ..logger import error_catcher
from .. import utils
from .tables import Customer_Providers_Table, Peers_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class CSV_Types(Enum):
    """Types of CSVs"""

    CUSTOMER_PROVIDERS = "Customer_Providers"
    PEERS = "Peers"

class Relationship_File:
    """File class that allows for download, unzip, and database storage
    The Relationship File Class allows for the downloading, unzipping, and
    database storage of Relationship files and data. After each step the
    unnessecary files are deleted.
    """

    __slots__ = ['path', 'url', 'logger', 'csv_directory', 'test', 'csv_names',
                 'divisor', 'name', 'rows']

    @error_catcher()
    def __init__(self, logger, path, csv_directory, url, test=False):
        """Initializes file instance and determine info about it"""

        self.logger = logger
        # names file
        self.name = "relationships.bz2"
        # os.path.join is neccessary for cross platform compatability
        self.path = os.path.join(path, self.name)
        self._url_rename(url)
        self.csv_directory = csv_directory
        self.test = test
        self.csv_names = {}
        self.divisor = re.compile(r'([^|\n\s]+)')
        self.logger.debug("Initialized file instance")

    @error_catcher()
    def parse_file(self, db=True):
        """Calls all functions to parse a file into the db"""

        # If the file wasn't downloaded, download it
        if not os.path.isfile(self.path):
            utils.download_file(self.logger,
                                self.url,
                                self.path,
                                1,  # File number
                                1)  # Total number of files
        self._unzip()
        # Gets data and writes it to the csvs
        self._write_csvs()
        # If db is false results are not inserted into the database
        if db:
            self._db_insert()
        # Deletes all paths/files that could have been created
        utils.delete_paths(self.logger, [self.csv_directory, self.path])

    def _url_rename(self, url):
        """Renames the url properly"""

        if "as-rel2" in url:
            self.url = "http://data.caida.org/datasets/as-relationships/serial-2/{}".format(url)
        elif "as-rel" in url:
            self.url = "http://data.caida.org/datasets/as-relationships/serial-1/{}".format(url)

    @error_catcher()
    def _unzip(self):
        """Unzips this .bz2 file"""

        old_path = self.path
        self.path = os.path.join("{}.decompressed".format(
                old_path[:-4]))
        self.name = "relationships.decompressed"
        utils.unzip_bz2(self.logger, old_path, self.path)

    @error_catcher()
    def _write_csvs(self):
        """Writes both csv files needed"""

        self._get_data()
        
        # For each type of csv:
        for _, val in CSV_Types.__members__.items():
            # Set the csv names
            self.csv_names[val] = "{}/{}_{}.csv".format(
                self.csv_directory, self.name[:-13], val)

            # Writes to the csvs
            utils.write_csv(self.logger,
                            self.rows.get(val),
                            self.csv_names.get(val))
        # Deletes the old path
            utils.delete_paths(self.logger, self.path)

    @error_catcher()
    def _db_insert(self):
        """Inserts all csvs into the database"""

        # Sets table names for database for each csv type
        table_names = {CSV_Types.CUSTOMER_PROVIDERS:
                           Customer_Providers_Table(self.logger),
                       CSV_Types.PEERS: Peers_Table(self.logger)}

        # Inserts the csvs into db and deletes them
        for _, val in CSV_Types.__members__.items():
            utils.csv_to_db(self.logger,
                            table_names.get(val),
                            self.csv_names.get(val))

    def _get_data(self):
        """Method to be inherited by class"""

        self.rows = {CSV_Types.CUSTOMER_PROVIDERS: [],
                     CSV_Types.PEERS: []}
        f = open(self.path, "r")
        lines = f.readlines()
        f.close()
        [self._parse_line(x) for x in lines if "#" not in x]
        self.logger.info("Parsed through file: {}".format(self.path))

class AS_File(Relationship_File):
    """AS_File, inherites from Relationship_File"""

    __slots__ = []

    def __init__(self, path, csv_directory, url, logger, test=False):
        """Initializes file instance and determine info about it"""

        Relationship_File.__init__(self, path, csv_directory, url, logger, test)

    def _parse_line(self, line):
        """parses a line for the csv files
        Format of an as_rel file:
        <provider_as> | <customer_as> | -1
        <peer_as> | <peer_as> | 0
        """

        nums = self.divisor.findall(line)
        classifier = nums[2]
        if classifier == '-1':
            self.rows.get(CSV_Types.CUSTOMER_PROVIDERS).append(
                [nums[0], nums[1]])
        elif classifier == '0':
            self.rows.get(CSV_Types.PEERS).append([nums[0], nums[1]])
        else:
            raise Exception("classifier unknown: {}".format(classifier))
        

class AS_2_File(Relationship_File):
    """AS_2 file, inherites from Relationship_file"""

    __slots__ = ['parse_duplicates']

    def __init__(self, path, csv_directory, url, logger, test=False):
        """Initializes file instance and determine info about it"""

        Relationship_File.__init__(self, path, csv_directory, url, logger, test)

    def _parse_line(self, line):
        """parses a line for the csv files
        Format of an as_rel file:
        <provider_as> | <customer_as> | -1
        <peer_as> | <peer_as> | 0 | <source>
        """

        groups = self.divisor.findall(line)
        classifier = groups[2]
        if classifier == '-1':
            self.rows.get(CSV_Types.CUSTOMER_PROVIDERS).append([groups[0], groups[1]])
        elif classifier == '0':
            self.rows.get(CSV_Types.PEERS).append([groups[0], groups[1]])
        else:
            raise Exception("classifier unknown: {}".format(classifier))
