#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables for the relationships tables

This module contains the relationships tables, which inherit from the
database class
"""

from psycopg2.extras import RealDictCursor
from ..logger import error_catcher
from ..database import Database

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
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the Customer Provider table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS customer_providers (
                  customer_providers_id serial PRIMARY KEY,
                  provider_as bigint,
                  customer_as bigint
                  );"""
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_customer_providers (
              test_customer_providers_id serial PRIMARY KEY,
              random_num int
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Drops all duplicates from the table"""

        self.logger.info("About to delete duplicates in customer providers")
        sql = """DELETE FROM customer_providers a USING customer_providers b
                 WHERE a.customer_providers_id < b.customer_providers_id AND a.provider_as = b.provider_as
                 AND a.customer_as = b.customer_as;"""
        self.cursor.execute(sql)
        self.logger.info("Duplicates deleted in customer providers")

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Clearing customer_providers")
        self.cursor.execute("DELETE FROM customer_providers")
        self.logger.info("customer_providers cleared")

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['provider_as', 'customer_as']

    @property
    def table(self):
        """Returns the table name"""

        return "customer_providers"


class Peers_Table(Database):
    """Peers Table class, inherits from Database"""

    __slots__ = ['logger', 'config', 'conn', 'cursor', 'test']

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the peers table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS peers (
                  peers_id serial PRIMARY KEY,
                  peer_as_1 bigint,
                  peer_as_2 bigint
                  );"""
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_peers (
              test_peers_id serial PRIMARY KEY,
              random_num int
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Drops all duplicates from the table"""

        self.logger.info("About to delete duplicates from peers")
        sql = """DELETE FROM peers a USING peers b
                 WHERE a.peers_id < b.peers_id AND a.peer_as_1 = b.peer_as_1
                 AND a.peer_as_2 = b.peer_as_2;"""
        self.cursor.execute(sql)
        self.logger.info("Deleted duplicates from peers")

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Clearing peers")
        self.cursor.execute("DELETE FROM peers")
        self.logger.info("peers cleared")

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['peer_as_1', 'peer_as_2']

    @property
    def table(self):
        """Returns the table name"""

        return "peers"
