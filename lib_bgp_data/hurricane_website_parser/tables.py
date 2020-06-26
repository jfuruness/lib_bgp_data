#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a bgp.he.net table

These tables must all inherit from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. Each table
follows the table name followed by a _Table since it inherits from the
database class.

Design choices:
    - This table is usually only combined with hurricane table, for which
      an index is created on the origin_as attribute

Possible future improvements:
    - Add test cases
"""

__author__ = "Samarth Kasbawala"
__credits__ = ["Samarth Kasbawala"]
__Licenece__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import logging

from ..database import Generic_Table


class Hurricane_Table(Generic_Table):
    """Hurricane_Table class

    For a more in depth explanation, see the top of the file
    """

    __slots__ = []
    name = "hurricane"
    columns = ["origin_as", "prefix", "description"]

    def _create_tables(self):
        """Create the table if it does not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS hurricane (
              origin_as varchar(15),
              prefix cidr,
              description text);
              """
        self.execute(sql)

    def create_index(self):
        """Creates an index on origin_as"""

        logging.debug("Creating index on hurricane table")
        sql = """CREATE INDEX IF NOT EXISTS hurricane_index ON hurricane 
              (origin_as);"""
        self.execute(sql)

