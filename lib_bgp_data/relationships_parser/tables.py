#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for relationship data tables

The relationship classes inherits from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function since this data is only used by
the extrapolator, which does not use indexes. Each table follows the
table name followed by a _Table since it inherits from the Database
class. In addition, since this data is used for the rovpp simulation,
there are also rovpp tables

Design choices:
    -There is no index creation function since indexes are never used
     for the typical purpose of the relationship data

Possible future improvements:
    -Add test cases
    -The data is actualy provider customers, change the name to
     provider_customers in this file and all others
"""


from ..utils import error_catcher, Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Customer_Providers_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger):
        """Initializes the Customer Provider table"""

        Database.__init__(self, logger)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS customer_providers;")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS customer_providers (
              provider_as bigint,
              customer_as bigint
              );"""
        self.cursor.execute(sql)


class Peers_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger):
        """Initializes the Peers table"""

        Database.__init__(self, logger)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS peers;")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS peers (
              peer_as_1 bigint,
              peer_as_2 bigint
              );"""
        self.cursor.execute(sql)

class ROVPP_Customer_Providers_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger):
        """Initializes the ROVPP Customer Provider table"""

        Database.__init__(self, logger)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_customer_providers;")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_customer_providers (
              provider_as bigint,
              customer_as bigint
              );"""
        self.cursor.execute(sql)


class ROVPP_Peers_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger):
        """Initializes the ROVPP Peers table"""

        Database.__init__(self, logger)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_peers;")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_peers (
              peer_as_1 bigint,
              peer_as_2 bigint
              );"""
        self.cursor.execute(sql)
