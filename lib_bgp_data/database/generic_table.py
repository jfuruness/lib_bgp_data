#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database and context manager db_connection

The Generic Table class can interact with a database. It can also be
inherited to allow for its functions to be used for specific tables in
the database. Other Table classes inherit the database class to be used
in utils functions that write data to the database. To do this, the
class that inherits the database must be named the table name plus
_Table. For more information on how to do this and other features, see the README on how to
add a submodule.

Note that all tables should have:
_create_tables - this creates empty tables. Sometimes unessecary, don't always need
fill_table - fills table with data, sometimes unessecary
clear_table - inherited, clears table

There are also some convenience funcs, documented below
"""

# Document the convenience funcs in readme!


import warnings
from multiprocessing import cpu_count
from subprocess import check_call
import os
import time
from .database import Database


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# SHOULD INHERIT DECOMETA!

class Generic_Table(Database):
    """Interact with the database"""

    __slots__ = []

    def __init__(self, *args, **kwargs):
        """Asserts that name is set"""

        assert hasattr(self, "name"), "Inherited class MUST have a table name attr"
        super(Generic_Table, self).__init__(self, *args, **kwargs)

    def get_all(self):
        """Gets all rows from table"""

        return self.execute("SELECT * FROM {}".format(self.name))

    def get_count(self, sql=None):
        """Gets count from table"""

        sql = sql if sql else "SELECT COUNT(*) FROM {}".format(self.name)
        return self.execute(sql)[0]["count"]


    def clear_table(self):
        """Clears the table"""

        self.logger.debug(f"Dropping {self.name} Table")
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.name}")
        self.logger.debug(f"{self.name} Table dropped")

    def copy_table(self, path: str):
        """Copies table to a specified path"""

        self.logger.debug(f"Copying file from {self.name} to {path}")
        self.execute(f"COPY {self.name} TO %s DELIMITER '\t';", [path])
        self.logger.debug("Copy complete")

    @property
    def columns(self):
        """Returns the columns of the table

        used in utils to insert csv into the database"""

        sql = """SELECT column_name FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = %s;
              """
        self.cursor.execute(sql, [self.name])
        # Make sure that we don't get the _id columns
        return [x['column_name'] for x in self.cursor.fetchall()
                if "_id" not in x['column_name']]
