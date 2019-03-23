#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROAs Collector to download/store ROAs from rpki"""

import requests
import urllib
import json
import re
import csv
from ..logger import Logger, error_catcher
from .. import utils
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
        utils.set_common_init_args(self, args, "Roas")
        self.csv_path = "{}/roas.csv".format(self.csv_dir)

    @error_catcher()
    @utils.run_parser()
    def parse_roas(self, db=True):
        """Downloads and stores roas from a json"""

        utils.write_csv(self.logger,
                        self._format_roas(self._get_json_roas()),  # Gets Roas
                        self.csv_path)
        utils.csv_to_db(self.logger, ROAs_Table(self.logger), self.csv_path)

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
        # Formats request
        req = urllib.request.Request(url, headers=headers)
        # Opens request
        with urllib.request.urlopen(req) as url:
            # Gets data from the json in the url
            return json.loads(url.read().decode())["roas"]

    @error_catcher()
    def _format_roas(self, unformatted_roas):
        """Format the roas to be input to a csv"""

        # I know you can use a list comp here but it's messy
        # Formats roas for csv
        formatted_roas = []
        for roa in unformatted_roas:
            formatted_roas.append(
                [int(re.findall('\d+', roa["asn"])[0]),  # Gets ASN
                 roa["prefix"],
                 int(roa["maxLength"])
                 ]) 
        return formatted_roas
