#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for blacklist tables.

All of these tables inherit from the Database class, initalizing any
tables necessary if they do not exist using _create_tables.
The class can also clear the table and do other functions.
"""

__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import logging
from ...utils.database import Generic_Table


class Blacklist_Table(Generic_Table):
    """blacklisted ASN table class"""

    __slots__ = []

    name = "blacklist"

    columns = ["asn", "source"]

    def _create_tables(self):
        """ Creates the table if it does not exist"""
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS blacklist(
                asn INTEGER,
                source TEXT) ;"""
        self.execute(sql)

    def create_index(self):
        """Creates index for table"""
        logging.debug("Creating index on blacklist")
        sql = """CREATE INDEX IF NOT EXISTS blacklist_index
              ON blacklist (asn)"""
        self.execute(sql)
