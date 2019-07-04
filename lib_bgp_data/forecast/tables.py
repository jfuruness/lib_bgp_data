#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from multiprocessing import Process, cpu_count
from ..utils import Database, db_connection, error_catcher, Config, utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class MRT_W_Roas_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.clear_table()
        self.unhinge_db()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              mrt_w_roas AS (
              SELECT m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN roas r ON m.prefix <<= r.prefix
              );"""
        self.cursor.execute(sql)
        self.rehinge_db()

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Dropping MRT_W_Roas")
        self.cursor.execute("DROP TABLE IF EXISTS mrt_w_roas")
        self.logger.info("MRT_W_Roas table dropped")

    def create_index(self):
        """Creates an index"""

        self.logger.info("Creating index")
        sql = """CREATE INDEX IF NOT EXISTS mrt_w_roas_index
                 ON mrt_w_roas USING GIST (prefix inet_ops);"""
        self.cursor.execute(sql)
        self.logger.info("Index created")

    @error_catcher()
    def drop_mrt_async(self):
        """Function that drops the mrt table to be called in multiprocess"""

        with db_connection(Database, self.logger) as db:
            self.logger.info("About to drop mrt announcements")
            db.cursor.execute("DROP TABLE mrt_announcements;")
            self.logger.info("Dropped mrt announcements")
            self.logger.info("About to drop roas")
            db.cursor.execute("DROP TABLE roas;")
            self.logger.info("Dropped roas")
            self.logger.info("About to vacuum")
#            db.cursor.execute("VACUUM;")###############################
            self.logger.info("Vacuum complete")
