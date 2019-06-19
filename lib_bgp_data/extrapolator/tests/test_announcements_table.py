#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the Announcements_Table class"""


import os
import unittest
import logging
from collections import Counter
from .test_database import TestDatabase
from ..logger import Logger
from ..database import Announcements_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class TestAnnouncements_Table(TestDatabase):
    """Tests Announcements_table class, inherits tests from TestDatabase"""

    def setUp(self):
        """Initializes db and connects"""

        # Up the logging level so we don't get useless info
        args = {"stream_level": logging.ERROR}
        self.db = Announcements_Table(self._initialize_logger(args=args))

    def test_init(self):
        """tests connection"""

        pass

    def test_create_tables(self):
        """Tests creation of tables"""

        self.db._create_tables()

    def test_columns(self):
        """Makes sure columns are correct"""

        sql = """select column_name from information_schema.columns where
              table_schema='public' and table_name='mrt_announcements';
              """
        cols = self.db.execute(sql)
        print(cols)
        cols = cols[0]
        cols = [key for key in cols if 'id' not in key]
        cols = cols.sort()
        cols_2 = self.db.columns.sort()
        # self.db.logger.error(cols.sort())
        # self.db.logger.error(self.db.columns.sort())
        self.assertTrue(Counter(cols) == Counter(cols_2))
