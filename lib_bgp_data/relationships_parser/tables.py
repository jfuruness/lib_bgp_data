#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables for the relationships tables

This module contains the relationships tables, which inherit from the
database class
"""

from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Customer_Providers_Table(Database):
    """Customer Providers table class, inherits from database"""

    __slots__ = ['logger', 'config', 'conn', 'cursor', 'test']

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor):
        """Initializes the Customer Provider table"""

        Database.__init__(self, logger, cursor_factory)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.cursor.execute("DROP TABLE IF EXISTS customer_providers;")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS customer_providers (
              provider_as bigint,
              customer_as bigint
              );"""
        self.cursor.execute(sql)

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['provider_as', 'customer_as']

    @property
    def name(self):
        """Returns the table name"""

        return "customer_providers"

class Peers_Table(Database):
    """Peers Table class, inherits from Database"""

    __slots__ = ['logger', 'config', 'conn', 'cursor', 'test']

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor):
        """Initializes the peers table"""
        Database.__init__(self, logger, cursor_factory)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.cursor.execute("DROP TABLE IF EXISTS peers;")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS peers (
              peer_as_1 bigint,
              peer_as_2 bigint
              );"""
        self.cursor.execute(sql)

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['peer_as_1', 'peer_as_2']

    @property
    def name(self):
        """Returns the table name"""

        return "peers"
