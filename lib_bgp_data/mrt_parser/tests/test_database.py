#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the Database class"""


import os
import unittest
import logging
from ..logger import Logger
from ..database import Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class TestDatabase(unittest.TestCase, Logger):
    """Tests the Database class"""

    # I know we could set up class but this seems more robust
    def setUp(self):
        """Initializes db and connects"""

        # Up the stream level so we don't get useless info
        args = {"stream_level": logging.ERROR}
        self.db = Database(self._initialize_logger(args=args))

    def tearDown(self):
        """Closes db connections"""

        self.db.close()
        logging.shutdown()

    def test_init_connect_close(self):
        """Tests init connect close through setUp tearDown"""

        pass

    def test_execute(self):
        """Tests execution of an arbitrary sql query with data and without"""

        try:
            # Tests execute with no data
            self._create_test_table()
            # Tests execute with data
            self.db.execute("""INSERT INTO test_bgp_mrt
                            (random_num) VALUES (%s)
                            RETURNING test_bgp_mrt_id
                            ;""", [1])
            # Tests fetchall within execute
            sql = "SELECT * FROM test_bgp_mrt WHERE random_num=1"
            self.assertTrue(self.db.execute(sql) not in [[], None])
            sql = "SELECT * FROM test_bgp_mrt WHERE random_num=2"
            self.assertTrue(self.db.execute(sql) in [[], None])
        except Exception as e:
            raise e
        finally:
            self._remove_test_table()

    def _create_test_table(self):
        """Creates a table to test with"""
        sql = """CREATE TABLE IF NOT EXISTS test_bgp_mrt (
              test_bgp_mrt_id serial PRIMARY KEY,
              random_num int
              );"""
        self.db.execute(sql)

    def _remove_test_table(self):
        """Removes test table"""

        sql = """DROP TABLE IF EXISTS test_bgp_mrt;"""
        self.db.execute(sql)
