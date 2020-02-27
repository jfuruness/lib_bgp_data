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
"""

from ..utils import Database

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

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS mrt_announcements (
                 prefix cidr,
                 as_path bigint ARRAY,
                 origin bigint,
                 time bigint
                 );"""
        self.cursor.execute(sql)

    def filter_by_IPV_family(self, IPV4: bool, IPV6: bool):
        """Filters the data by IPV family"""

        self.logger.info("Filtering by IPV family")
        for num, ipv_bool in zip([4, 6], [IPV4, IPV6]):
            if not ipv_bool:
                self.logger.debug(f"Deleting IPV{num} from {self.name}")
                sql = f"DELETE FROM {self.name} WHERE family(prefix) = {num};"
                self.execute(sql)
                self.logger.debug(f"IPV{num} deleted from mrt_announcements")
