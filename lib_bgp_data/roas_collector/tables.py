#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables classes to store roas"""

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

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS roas (
                  roas_id serial PRIMARY KEY,
                  asn bigint,
                  prefix inet,
                  max_length integer
                  );"""
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_roas (
              test_roas_id serial PRIMARY KEY,
              random_num int
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Clearing Roas")
        self.cursor.execute("DELETE FROM roas")
        self.logger.info("ROAs Table Cleared")

    @property
    def table(self):
        """Returns the name of the table"""

        return "roas"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['asn',
                'prefix',
                'max_length'
                ]
