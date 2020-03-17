#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Generic Table

The Generic Table class can interact with a database. It can also be
inherited to allow for its functions to be used for specific tables in
the database. Other Table classes inherit the database class to be used
in utils functions that write data to the database. To do this, the
class that inherits the database must be named the table name plus
_Table. For more information on how to do this and other features, see the README on how to
add a submodule.

Note that all tables should have:
_create_tables - this creates empty tables. Sometimes unessecary, don't always need
create_index - creates an index on the table
fill_table - fills table with data, sometimes unessecary
clear_table - inherited, clears table

There are also some convenience funcs, documented below
"""

# Document the convenience funcs in readme!

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import inspect
import warnings
import logging
from multiprocessing import cpu_count
from subprocess import check_call
import os
import time

from .database import Database


# SHOULD INHERIT DECOMETA!

class Generic_Table(Database):
    """Interact with the database"""

    __slots__ = ["name"]

    def __init__(self, *args, **kwargs):
        """Asserts that name is set

        Makes sure sql queries are formed properly"""

        assert hasattr(self, "name"), "Inherited class MUST have a table name attr"
        unlogged_err = ("Create unlogged tables for speed.\n Ex:"
                        "CREATE UNLOGGED TABLE IF NOT EXISTS {self.name}...")
        # https://stackoverflow.com/a/427533/8903959
        if "create table" in inspect.getsource(self.__class__):
            raise Exception(unlogged_err + "\n And also capitalize SQL")
        if "CREATE TABLE" in inspect.getsource(self.__class__):
            raise Exception(unlogged_err)
        super(Generic_Table, self).__init__(*args, **kwargs)

    def get_all(self) -> list:
        """Gets all rows from table"""

        return self.execute(f"SELECT * FROM {self.name}")

    def get_count(self, sql: str = None) -> int:
        """Gets count from table"""

        sql = sql if sql else f"SELECT COUNT(*) FROM {self.name}"
        return self.execute(sql)[0]["count"]


    def clear_table(self):
        """Clears the table"""

        logging.debug(f"Dropping {self.name} Table")
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.name}")
        logging.debug(f"{self.name} Table dropped")

    def copy_table(self, path: str):
        """Copies table to a specified path"""

        logging.debug(f"Copying file from {self.name} to {path}")
        self.execute(f"COPY {self.name} TO %s DELIBSDER '\t';", [path])
        logging.debug("Copy complete")

    def filter_by_IPV_family(self, IPV4: bool, IPV6: bool, col="prefix"):
        """Filters the data by IPV family"""

        logging.info("Filtering by IPV family")
        for num, ipv_bool in zip([4, 6], [IPV4, IPV6]):
            if not ipv_bool:
                logging.debug(f"Deleting IPV{num} from {self.name}")
                sql = f"DELETE FROM {self.name} WHERE family({col}) = {num};"
                self.execute(sql)
                logging.debug(f"IPV{num} deleted from mrt_announcements")

    @property
    def columns(self) -> list:
        """Returns the columns of the table

        used in utils to insert csv into the database"""

        sql = """SELECT column_name FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = %s;
              """
        self.cursor.execute(sql, [self.name])
        # Make sure that we don't get the _id columns
        return [x['column_name'] for x in self.cursor.fetchall()
                if "_id" not in x['column_name']]
