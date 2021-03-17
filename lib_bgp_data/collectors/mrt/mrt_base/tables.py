#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Announcements_Table

Announcements_Table inherits from the Generic_Table class. The Generic_Table
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

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

from ....utils.database import Generic_Table


class MRT_Announcements_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "mrt_announcements"

    columns = ["prefix", "as_path", "origin", "time"]

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                 prefix INET,
                 as_path bigint ARRAY,
                 origin BIGINT,
                 time BIGINT
                 );"""
        self.execute(sql)
