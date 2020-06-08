#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for blacklist tables.

All of these tables inherit from the Database class, initalizing any tables necessary if they do not exist using the _create_tables function. The class can also clear the table and do other functions
"""

__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import logging
from ..database import Generic_Table

class Blacklist_Table(Generic_Table):
    """blacklisted ASN table class"""

    __slots__ = []

    name = "blacklist"

    def _create_tables(self):
        """ Creates the table if it does not exist"""
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS blacklist (uce2 integer, uce3 integer, spamhaus integer, mit integer) ;"""
        self.execute(sql)
    
    # The following removed as an index is not necessary, and might
    # cause more issues than it solves.
    #def create_index(self):
    #    """Creates indexes to be used on the table"""
    #    logging.debug("Created index for blacklist")
    #    sql = "CREATE INDEX IF NOT EXISTS blacklist_index ON blacklist USING HASH()"
    #    self.execute(sql)
