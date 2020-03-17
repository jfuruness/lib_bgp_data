#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationships_Parser

The purpose of this class is to download the relationship files and
insert the data into a database. See README for detailed steps.
"""

import warnings
from .relationships_file import Rel_File
from .tables import ASes_Table, AS_Connectivity_Table, Provider_Customers_Table
from ..base_classes import Parser
from ..utils import utils

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Relationships_Parser(Parser):
    """This class downloads, parses, and deletes files from Caida

    In depth explanation in README
    """

    def _run(self, *args, url=None):
        """Downloads and parses file

        In depth explanation at top of module. Aggregate months aggregates
        relationship data from x months ago into the same table
        """

        Provider_Customers_Table()
        
        url = url if url else self._get_urls()[0]
        Rel_File(self.path, self.csv_dir, url).parse_file()
        utils.delete_paths([self.csv_dir, self.path])

        # Fills these rov++ specific tables
        with ASes_Table(clear=True) as _as_table:
            _as_table.fill_table()
        # creates and closes table
        with AS_Connectivity_Table(clear=True) as _conn_table:
            _conn_table.fill_table()

########################
### Helper Functions ###
########################

    def _get_urls(self, months_back=0):
        """Gets urls to download relationship files and the dates.

        Months back is something we tried to do and was later removed
        since we did it wrong. Leaving it in for the next attempt.
        """

        # Api url
        prepend = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        # Get all html tags that might have links
        _elements = [x for x in utils.get_tags(prepend, 'a')]
        # Gets the last file of all bz2 files
        file_urls = [x["href"] for x in _elements if "bz2" in x["href"]]
        return [prepend + x for x in file_urls[-1 - months_back:]]

    def parse_files(self, **kwargs):
        warnings.warn(("Relationships_Parser.parse_files is depreciated. "
                       "Use Relationships_Parser.run instead"),
                      DeprecationWarning,
                      stacklevel=2)
        self.run(self, **kwargs)
