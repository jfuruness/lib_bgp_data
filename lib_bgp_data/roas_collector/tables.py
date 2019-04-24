#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables classes to store roas"""

from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROAs_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""

        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS roas (
              asn bigint,
              prefix inet,
              max_length integer
              ) ;"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Clearing Roas")
        self.cursor.execute("DROP TABLE IF EXISTS roas")
        self.logger.info("ROAs Table Cleared")

    @error_catcher()
    def create_index(self):
        """Creates a bunch of indexes to be used on the table"""

        self.logger.info("Creating index on roas")
        sqls = ["""CREATE INDEX IF NOT EXISTS roas_index
                ON roas USING GIST(prefix inet_ops)""",
               """CREATE INDEX IF NOT EXISTS roas_po_index
               ON roas USING GIST(prefix inet_ops, max_length)"""]
        for sql in sqls:
            self.cursor.execute(sql)

    @property
    def name(self):
        """Returns the name of the table"""

        return "roas"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['asn', 'prefix', 'max_length']
