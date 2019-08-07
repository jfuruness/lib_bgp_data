#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationships_File

The purpose of this class is to download the relationship files and
insert the data into a database. This is done through a series of steps.

1. The relationship file is downloaded
    -This is handled in the utils.download_file function
2. Then the file is unzipped
3. The relationship file is then split into two
    -This is handled in the Relationship_File class
    -This is done because the file contains both peers and
     customer_provider data.
    -The file itself is a formatted CSV with "|" delimiters
    -Using grep and cut the relationships file is split and formatted
    -This is done instead of regex because it is faster and simpler
    -For more specifics see _db_insert function
    -Note that for the rovpp extension an option is included to use those
     tables instead so as not to interfere with other ongoing work
4. Then each CSV is inserted into the database
    -Handled by utils.csv_to_db
    -The ROVPP simulation uses different tables, so different tables
     are passed in if that simulation is being run
    -The old table gets destroyed first
    -This is handleded in the utils.csv_to_db function
    -This is done because the file comes in CSV format
5. The csvs are then deleted

Design Choices:
    -CSV insertion is done because the relationships file is a CSV
    -Dates are stored and checked to prevent redoing old work
    -An enum was used to make the code cleaner
        -Classes are more messy in this case

Possible Future Extensions:
    -Add test cases
    -Possibly take out date checking for cleaner code?
     Saves very little time
    -Move unzip_bz2 to this file? Nothing else uses it anymore
"""

from enum import Enum
import os
from subprocess import call
from ..utils import utils, error_catcher
from .tables import Customer_Providers_Table, Peers_Table
from .tables import ROVPP_Customer_Providers_Table, ROVPP_Peers_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Rel_Types(Enum):
    """The two types of relationship data"""

    CUSTOMER_PROVIDERS = "customer_providers"
    PEERS = "peers"


class Rel_File:
    """File class that allows for download, unzip, and database storage.

    More in depth explanation at top of file.
    """

    __slots__ = ['path', 'url', 'logger', 'csv_dir', 'rovpp']

    @error_catcher()
    def __init__(self, path, csv_dir, url, logger):
        """Initializes file instance and assigns attributes"""

        self.logger = logger
        self.csv_dir = csv_dir
        # File will be called rel.bz2
        self.path = os.path.join(path, "rel.bz2")
        self.url = url

    @error_catcher()
    def parse_file(self, rovpp=False):
        """Calls all functions to parse a file into the db.

        For more in depth explanation see top of file."""

        # Downloads the file
        utils.download_file(self.logger, self.url, self.path)
        # Unzips file and assigns new path
        self.path = utils.unzip_bz2(self.logger, self.path)
        # Gets data and writes it to the csvs
        self._db_insert(rovpp)
        # Deletes all paths/files that could have been created
        utils.delete_paths(self.logger, [self.csv_dir, self.path])

    @error_catcher()
    def _db_insert(self, rovpp=False):
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

        grep, csvs, tables = self._get_rel_attributes(rovpp)

        # For each type of csv:
        for val in Rel_Types.__members__.values():
            # Grep the CSV based on relationship information into a CSV
            call("cat {} | {} > {}".format(self.path, grep[val], csvs[val]),
                 shell=True)
            # Inserts the CSV into the database
            utils.csv_to_db(self.logger, tables[val], csvs[val])
        # Deletes the old paths
        utils.delete_paths(self.logger, self.path)
        utils.delete_paths(self.logger, [val for key, val in csvs.items()])

    @error_catcher()
    def _get_rel_attributes(self, rovpp=False):
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
        _grep_temp = {Rel_Types.CUSTOMER_PROVIDERS:
                      'grep "\-1" | grep -F -v "#"',
                      Rel_Types.PEERS: 'grep -v "\-1" | grep -F -v "#"'}
        # Appended onto all grep strings to format for CSV insertion
        grep = {key: val + ' | cut -d "|" -f1,2 | sed -e "s/|/\t/g"'
                for key, val in _grep_temp.items()}
        # Paths for each csv
        csvs = {val: '{}/rel.csv'.format(self.csv_dir, val) for val in
                Rel_Types.__members__.values()}

        # The last value is the tables for csv insertion
        return grep, csvs, self._get_table_attributes(rovpp)

    @error_catcher()
    def _get_table_attributes(self, rovpp=False):
        """Returns tables to be used for CSV insertion.

        if the simulation is for rovpp then rov tables are used.
        """

        # For the ROVPP simulation
        if rovpp:
            return {Rel_Types.CUSTOMER_PROVIDERS:
                    ROVPP_Customer_Providers_Table,
                    Rel_Types.PEERS: ROVPP_Peers_Table}
        # If it is for the other simulations we want these tables:
        else:
            return {Rel_Types.CUSTOMER_PROVIDERS: Customer_Providers_Table,
                    Rel_Types.PEERS: Peers_Table}
