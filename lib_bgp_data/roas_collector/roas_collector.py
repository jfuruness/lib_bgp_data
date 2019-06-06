#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROAs Collector to download/store ROAs from rpki"""

import requests
import urllib
import json
import re
import csv
from ..utils import utils, error_catcher, db_connection
from .tables import ROAs_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROAs_Collector:
    """This class downloads, and stores ROAs from rpki validator""" 

    __slots__ = ['path', 'csv_dir', 'args', 'logger', 'csv_path', 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)
        self.csv_path = "{}/roas.csv".format(self.csv_dir)

    @error_catcher()
    @utils.run_parser()
    def parse_roas(self, db=True):
        """Downloads and stores roas from a json"""

        with db_connection(ROAs_Table, self.logger) as roas_table:
            roas_table.clear_table()
            roas = self._format_roas(self._get_json_roas())
            utils.rows_to_db(self.logger, roas, self.csv_path, ROAs_Table)
            roas_table.create_index()

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_json_roas(self):
        """Returns the json from the url for the roas"""

        # Request URL
        url = "https://rpki-validator.ripe.net/api/export.json"
        # Need these headers so that the xml can be accepted
        headers = {"Accept":"application/xml;q=0.9,*/*;q=0.8"}
        # Gets the roas from the json
        return utils.get_json(url, headers)["roas"]

    @error_catcher()
    def _format_roas(self, unformatted_roas):
        """Format the roas to be input to a csv"""

        # Returns a list of lists of formatted roas
        # Formats roas for csv
        return [[int(re.findall('\d+', roa["asn"])[0]),  # Gets ASN
                 roa["prefix"],
                 int(roa["maxLength"])]
                for roa in unformatted_roas]
