#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationships_File

The purpose of this class is to download the relationship files and
insert the data into a database. For a more detailed explanation see README.
"""

from enum import Enum
import logging
import os

from .tables import Provider_Customers_Table, Peers_Table
from ..base_classes import File
from ..utils import utils

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Rel_Types(Enum):
    """The two types of relationship data"""

    PROVIDER_CUSTOMERS = "provider_customers"
    PEERS = "peers"


class Rel_File(File):
    """File class that allows for download, unzip, and database storage.

    More in depth explanation at top of file.
    """

    __slots__ = []

    def parse_file(self):
        """Calls all functions to parse a file into the db.

        For more in depth explanation see top of file."""

        # Downloads the file
        utils.download_file(self.url, self.path)
        # Unzips file and assigns new path
        self.path: str = utils.unzip_bz2(self.path)
        # Gets data and writes it to the csvs
        self._db_insert()

    def _db_insert(self):
        """Writes both csv files needed and insert into the database.

        First get the attributes of each relationship type. This
        includes the string used to grep the original file, the csv path
        and also the table name. Then for each of the relationship types
        cat the original file, grep for either customer_provider or peer
        relationships, and put it into a CSV file. Then insert that CSV
        into the database, and delete all old files. For a more in depth
        explanation see the top of the file. For how each specific CSV
        is formatted see below:

        <provider-as>|<customer-as>|-1
        <peer-as>|<peer-as>|0|<source>
        """

        grep, csvs, tables = self._get_rel_attributes()

        # For each type of csv:
        for key in Rel_Types.__members__.values():
            # Grep the CSV based on relationship information into a CSV
            utils.run_cmds(f"cat {self.path} | {grep[key]} > {csvs[key]}")
            # Inserts the CSV into the database
            utils.csv_to_db(tables[key], csvs[key], clear_table=True)
        # Deletes the old paths
        utils.delete_paths([self.path, self.csv_dir])

    def _get_rel_attributes(self):
        """Returns the grep string, csv path, and table attributes.

        The grep strings first filter based on whether the information
        is a customer_provider pair or a peer pair. If there is a -1 it
        is customer provider data, else it is peer data. If there is a #
        that is a comment and shouldn't be included in a csv. cat is
        called and gets piped into the grep strings, which then get
        piped into cut which removes unnessecary information, and then
        is piped into sed to produce a tab delimited CSV. The csvs are
        the paths to each csv file, and the tables are for insertion
        later. This is put here instead of init or having classes in the
        enum for cleaner code, other methods get a little messy.
        """

        # The start of the grep strings
        _grep_temp = {Rel_Types.PROVIDER_CUSTOMERS:
                      'grep "\-1" | grep -F -v "#"',
                      Rel_Types.PEERS: 'grep -v "\-1" | grep -F -v "#"'}
        # Appended onto all grep strings to format for CSV insertion
        grep = {key: val + ' | cut -d "|" -f1,2 | sed -e "s/|/\t/g"'
                for key, val in _grep_temp.items()}
        # Paths for each csv
        csvs = {key: f'{self.csv_dir}/{key.value}_rel.csv' for key in
                Rel_Types.__members__.values()}

        # The last value is the tables for csv insertion
        return grep, csvs, self._get_table_attributes()

    def _get_table_attributes(self):
        """Returns tables to be used for CSV insertion"""

        return {Rel_Types.PROVIDER_CUSTOMERS: Provider_Customers_Table,
                Rel_Types.PEERS: Peers_Table}
