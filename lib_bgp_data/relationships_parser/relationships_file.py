#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationship_File

The MRT File Class allows for the downloading, unzipping, and database
storage of MRT files and data. After each step the unnessecary files are
deleted.
"""

from enum import Enum
import re
import os
from subprocess import call
from ..utils import utils, error_catcher
from .tables import Customer_Providers_Table, Peers_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

# The two types of relationship data
class Rel_Types(Enum):
    CUSTOMER_PROVIDERS = "customer_providers"
    PEERS = "peers"

class Rel_File:
    """File class that allows for download, unzip, and database storage
    The Relationship File Class allows for the downloading, unzipping, and
    database storage of Relationship files and data. After each step the
    unnessecary files are deleted.
    """

    __slots__ = ['path', 'url', 'logger', 'csv_dir']

    @error_catcher()
    def __init__(self, path, csv_dir, url, logger):
        """Initializes file instance and determine info about it"""

        self.logger = logger
        self.csv_dir = csv_dir
        self.path = os.path.join(path, "rel.bz2")
        self.url = url

    @error_catcher()
    def parse_file(self):
        """Calls all functions to parse a file into the db"""

        utils.download_file(self.logger, self.url, self.path)
        self.path = utils.unzip_bz2(self.logger, self.path)
        # Gets data and writes it to the csvs
        self._db_insert()
        # Deletes all paths/files that could have been created
        utils.delete_paths(self.logger, [self.csv_dir, self.path])

    @error_catcher()
    def _db_insert(self):
        """Writes both csv files needed"""

        grep, csvs, tables = self._get_rel_attributes()

        # For each type of csv:
        for val in Rel_Types.__members__.values():
            call("cat {} | {} > {}".format(self.path, grep[val], csvs[val]),
                 shell=True)
            utils.csv_to_db(self.logger, tables[val], csvs[val])
        # Deletes the old paths
        utils.delete_paths(self.logger, [self.path].extend([val for key, val in csvs.items()]))

    @error_catcher()
    def _get_rel_attributes(self):
        """Put here instead of _db_insert or __init__ for cleaner code, if you don't do it this way it starts to get pretty messy"""

        grep = {Rel_Types.CUSTOMER_PROVIDERS: 'grep "\-1" | grep -F -v "#" | cut -d "|" -f1,2 | sed -e "s/|/\t/g"',
                Rel_Types.PEERS: 'grep -v "\-1" | grep -F -v "#" | cut -d "|" -f1,2 | sed -e "s/|/\t/g"'}
        csvs = {val: '{}/rel.csv'.format(self.csv_dir, val) for val in
                Rel_Types.__members__.values()}
        tables = {Rel_Types.CUSTOMER_PROVIDERS: Customer_Providers_Table,
                       Rel_Types.PEERS: Peers_Table}
        return grep, csvs, tables
