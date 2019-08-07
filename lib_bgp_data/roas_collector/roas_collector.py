#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROAs Collector

The purpose of this class is to download ROAs from rpki and insert them
into a database. This is done through a series of steps.

1. Clear the Roas table
    -Handled in the parse_roas function
2. Make an API call to https://rpki-validator.ripe.net/api/export.json
    -Handled in the _get_json_roas function
    -This will get the json for the roas
3. Format the roa data for database insertion
    -Handled in the _format_roas function
4. Insert the data into the database
    -Handled in the utils.rows_to_db
    -First converts data to a csv then inserts it into the database
    -CSVs are used for fast bulk database insertion
5. An index is created on the roa prefix
    -The purpose of this is to make the SQL query faster when joining
     with the mrt announcements

Design Choices (summarizing from above):
    -CSVs are used for fast database bulk insertion
    -An index on the prefix is created on the roas for fast SQL joins

Possible Future Extensions:
    -Add test cases
"""


import re
from ..utils import utils, error_catcher, db_connection
from .tables import ROAs_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROAs_Collector:
    """This class downloads, and stores ROAs from rpki validator"""

    __slots__ = ['path', 'csv_dir', 'logger', 'csv_path']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)
        self.csv_path = "{}/roas.csv".format(self.csv_dir)

    @error_catcher()
    @utils.run_parser()
    def parse_roas(self):
        """Downloads and stores roas from a json

        For more in depth explanation see top of file"""

        with db_connection(ROAs_Table, self.logger) as _roas_table:
            roas = self._format_roas(self._get_json_roas())
            # Inserts the data into a CSV and then the database
            utils.rows_to_db(self.logger, roas, self.csv_path, ROAs_Table)
            # Creates an index on the roas table prefix
            _roas_table.create_index()

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_json_roas(self):
        """Returns the json from the url for the roas"""

        # Request URL
        url = "https://rpki-validator.ripe.net/api/export.json"
        # Need these headers so that the xml can be accepted
        headers = {"Accept": "application/xml;q=0.9,*/*;q=0.8"}
        # Gets the roas from the json
        return utils.get_json(url, headers)["roas"]

    @error_catcher()
    def _format_roas(self, unformatted_roas):
        """Format the roas to be input to a csv"""

        # Returns a list of lists of formatted roas
        # Formats roas for csv
        return [[int(re.findall(r'\d+', roa["asn"])[0]),  # Gets ASN
                 roa["prefix"],
                 int(roa["maxLength"])]
                for roa in unformatted_roas]
