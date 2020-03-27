#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the table found on asrank.caida.org

These tables must all inherit from the Generic_Table class. The Generic_Table
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database.

Design choices:
    -Index will be created to find the top 100 as_numbers
    -The asrank table is always cleared when the asrank_website_parser is run

Possible future improvements:
    -Add test cases
"""


__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from ..database import Generic_Table


class ASRank_Table(Generic_Table):
    """ASRank table class, inherits from Generic_Table.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = 'asrank'

    def _create_tables(self):
        """Creates new table if it doesn't already exist. The contents will
        be cleared everytime asrank_website_parser is run because information
        in the datebase may be out of date.
        """
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS asrank (
              as_rank bigint,
              as_number bigint,
              organization varchar (250),
              country varchar (2),
              cone_size integer
              );"""
        self.cursor.execute(sql)

    def create_index(self):
        """Creates an index on top 100 AS numbers"""
        sql = """CREATE INDEX IF NOT EXISTS asrank_index ON as_rank
                  USING BTREE(as_number) WHERE as_rank <= 100;"""
        self.cursor.execute(sql)

    def print_top_100(self):
        sql = """SELECT * FROM asrank ORDER BY as_rank"""
        self.cursor.execute(sql)
        for i in range(100):
            print(self.cursor.fetchone())
