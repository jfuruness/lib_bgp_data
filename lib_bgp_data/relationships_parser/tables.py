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
            sql = """CREATE UNLOGGED TABLE IF NOT EXISTS customer_providers (
                  provider_as bigint,
                  customer_as bigint
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
    def name(self):
        """Returns the table name"""

        return "customer_providers"

    def create_index(self):
        """Creates index on customer providers"""

        sqls = ["""CREATE INDEX IF NOT EXISTS customer_providers_index_provider
                ON customer_providers (provider_as)""",
                """CREATE INDEX IF NOT EXISTS customer_providers_index_customer
                ON customer_providers (customer_as)"""]
        for sql in sqls:
            self.cursor.execute(sql)


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
            sql = """CREATE UNLOGGED TABLE IF NOT EXISTS peers (
                  peer_as_1 bigint,
                  peer_as_2 bigint
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
    def name(self):
        """Returns the table name"""

        return "peers"

    def create_index(self):
        """Creates indexes on the peers table"""

        sqls = ["""CREATE INDEX IF NOT EXISTS peers_1_index
                ON peers (peer_as_1)""",
                """CREATE INDEX IF NOT EXISTS peers_1_index
                ON peers (peer_as_2)"""]
        for sql in sqls:
            self.cursor.execute(sql)
