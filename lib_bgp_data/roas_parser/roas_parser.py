#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROAs Collector

The purpose of this class is to download ROAs from rpki and insert them
into a database. See README for in depth explanation
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Xinyu"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from copy import deepcopy
import re
import warnings
from .tables import ROAs_Table
from ..base_classes import Parser
from ..utils import utils


class ROAs_Parser(Parser):
    """This class downloads, and stores ROAs from rpki validator"""

    __slots__ = []

    def _run(self):
        """Downloads and stores roas from a json

        For more in depth explanation see README"""

        with ROAs_Table(clear=True) as _roas_table:
            roas = self._format_roas(self._get_json_roas())
            # Inserts the data into a CSV and then the database
            _csv_dir = f"{self.csv_dir}/roas.csv"
            utils.rows_to_db(roas, _csv_dir, ROAs_Table)
            # Creates an index on the roas table prefix
            _roas_table.create_index()

########################
### Helper Functions ###
########################

    def _get_json_roas(self):
        """Returns the json from the url for the roas"""

        # Request URL
        url = "https://rpki-validator.ripe.net/api/export.json"
        # Need these headers so that the xml can be accepted
        headers = {"Accept": "application/xml;q=0.9,*/*;q=0.8"}
        # Gets the roas from the json
        return utils.get_json(url, headers)["roas"]

    def _format_roas(self, unformatted_roas: dict) -> list:
        """Format the roas to be input to a csv"""

        # Returns a list of lists of formatted roas
        # Formats roas for csv
        return [[int(re.findall(r'\d+', roa["asn"])[0]),  # Gets ASN
                 roa["prefix"],
                 int(roa["maxLength"])]
                for roa in unformatted_roas]

    def parse_roas(self, **kwargs):
        warnings.warn(("ROAs_Collector.parse_roas is depreciated. "
                       "Use Roas_Parser.run instead"),
                      DeprecationWarning,
                      stacklevel=2)
        self.run(self, **kwargs)

class ROAs_Collector(ROAs_Parser):
    def __init__(self, **kwargs):
        warnings.warn(("ROAs_Collector is depreciated. "
                       "Use Roas_Parser instead"),
                       DeprecationWarning,
                       stacklevel=1)
        super(ROAs_Collector, self).__init__(**kwargs)
