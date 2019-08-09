#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Announcements_Table

Announcements_Table inherits from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function, because it would only ever be
used when combining with the roas table, which does a parallel seq_scan,
thus any indexes are not used since they are not efficient. Each table
follows the table name followed by a _Table since it inherits from the
database class.

Design choices:
    -There is no index creation function since indexes are never used
     for the typical purpose of the Announcements Table.
    -This table is usually only combined with the roas table, for which
     it uses a parallel seq_scan, with no indexes

Possible future improvements:
    -Add test cases
"""

from ..utils import Database, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class MRT_Announcements_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS mrt_announcements (
                 prefix cidr,
                 as_path bigint ARRAY,
                 origin bigint,
                 time bigint
                 ) ;"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the mrt_announcements table.

        Should be called at the start of every run.
        """

        self.logger.info("Dropping MRT Announcements")
        self.cursor.execute("DROP TABLE IF EXISTS mrt_announcements")
        self.logger.info("MRT Announcements Table dropped")

    @error_catcher()
    def filter_by_IPV_family(self, IPV4, IPV6):
        """Filters the data by IPV family"""

        if not IPV6:
            self.logger.info("Deleting IPV6 from mrt announcements")
            sql = "DELETE FROM mrt_announcements WHERE family(prefix) = 6;"
            self.cursor.execute(sql)
            self.logger.info("IPV6 deleted from mrt_announcements")
        if not IPV4:
            self.logger.info("Deleting IPV4 from mrt_announcements")
            sql = "DELETE FROM mrt_announcements WHERE family(prefix) = 4;"
            self.cursor.execute(sql)
            self.logger.info("IPV4 deleted from mrt_announcements")
