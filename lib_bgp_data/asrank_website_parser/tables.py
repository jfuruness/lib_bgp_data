#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains numerous bgpstream.com tables

These tables must all inherit from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. Each table
follows the table name followed by a _Table since it inherits from the
database class. These tables also contain functions that delete
duplicates, format tables for IPV4 or IPV6 data, and can create
subtables that are subsets of the data

Design choices:
    -Indexes are created on the times for the what if analysis
    -The asrank table is always created in its entirety everytime

Possible future improvements:
    -Add test cases
"""

from ..database import Generic_Table

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"


class ASRank_Table(Generic_Table):
    """ASRank table class, inherits from database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = 'asrank'

    def _create_tables(self):
        """Creates new table everytime because information
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
        """Creates an index on the times for later table creations
            Create index on the as_rank"""


        sql = """CREATE INDEX IF NOT EXISTS hijack_index ON hijack
                  USING BTREE(start_time, end_time);"""
        self.cursor.execute(sql)

    def print_top_100(self):
        sql = """SELECT * FROM asrank ORDER BY as_rank"""
        self.cursor.execute(sql)
        for i in range(100):
            print(self.cursor.fetchone())

   
