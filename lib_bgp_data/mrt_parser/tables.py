#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from ..config import Config
from ..logger import error_catcher
from ..database import Database

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

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE UNLOGGED TABLE IF NOT EXISTS mrt_announcements (
                  time timestamp,
                  prefix cidr,
                  as_path bigint ARRAY,
                  origin bigint
                  );"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Dropping MRT Announcements")
        self.cursor.execute("DROP TABLE mrt_announcements")
        self.logger.info("MRT Announcements Table dropped")

    def create_index(self):
        """Creates an index"""

        self.logger.info("Creating index")
        sql = """CREATE INDEX IF NOT EXISTS mrt_announcements_index
                 ON mrt_announcements USING GIST (prefix inet_ops);"""
        self.cursor.execute(sql)
        self.logger.info("Index created")

    @property
    def name(self):
        """Returns the name of the table"""

        return "mrt_announcements"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['time', 'prefix', 'as_path', 'origin']
