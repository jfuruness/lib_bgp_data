#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for Roas tables

All of these tables  inherits from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. Each table
follows the table name followed by a _Table since it inherits from the
database class.

Design choices:
    -This table is usually only combined with the roas table, for which
     an index is created on the prefix

Possible future improvements:
    -Add test cases
"""

from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROAs_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS roas (
              asn bigint,
              prefix cidr,
              max_length integer
              ) ;"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.debug("Clearing Roas")
        self.cursor.execute("DROP TABLE IF EXISTS roas")
        self.logger.debug("ROAs Table Cleared")

    @error_catcher()
    def create_index(self):
        """Creates a bunch of indexes to be used on the table"""

        self.logger.debug("Creating index on roas")
        sql = """CREATE INDEX IF NOT EXISTS roas_index
              ON roas USING GIST(prefix inet_ops)"""
        self.cursor.execute(sql)
