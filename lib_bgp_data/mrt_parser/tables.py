#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from .config import Config
from .logger import error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Announcements_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""
        Database.__init__(self, logger, cursor_factory, test)
        self.clear_table()

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS mrt_announcements (
                  mrt_announcements_id serial PRIMARY KEY,
                  peer_asn bigint,
                  peer_address inet,
                  as_path bigint ARRAY,
                  prefix inet,
                  next_hop inet,
                  time integer
                  );"""
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_bgp_mrt (
              test_bgp_mrt_id serial PRIMARY KEY,
              random_num int
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def _clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Clearing MRT Announcements")
        self.cursor.execute("DELETE FROM mrt_announcements")
        self.logger.info("MRT Announcements Table Cleared")

    @propert
    def name(self):
        """Returns the name of the table"""

        return "mrt_announcements"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['peer_asn',
                'peer_address',
                'as_path',
                'prefix',
                'next_hop',
                'time',
                ]
