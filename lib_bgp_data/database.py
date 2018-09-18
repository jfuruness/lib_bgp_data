#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

__author__ = "Justin Furuness"


import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from .as_relationships import AS_Relationship_DB
from .bgpstream import BGPStream_DB
from .announcements import Announcements_DB
from .config import Config
from .logger import Logger


class Database(AS_Relationship_DB, BGPStream_DB, Announcements_DB, Logger):
    """Interact with the database to populate them"""

    def __init__(self,
                 log_name="database.log",
                 log_file_level=logging.ERROR,
                 log_stream_level=logging.INFO,
                 cursor_factory=None
                 ):
        """Create a new connection with the databse"""

        # Function can be found in logger.Logger class
        # Initializes self.logger
        self._initialize_logger(log_name, log_file_level, log_stream_level)
        self.config = Config(self.logger)
        self.conn, self.cursor = self._connect(cursor_factory=cursor_factory)
        self.conn.autocommit = True

    def _connect(self, cursor_factory):
        """Connects to db"""

        username, password, host, database = self.config.get_db_creds()
        try:
            kwargs = {"user": username,
                      "password": password,
                      "host": host,
                      "database": database
                      }
            if cursor_factory:
                kwargs["cursor_factory"] = cursor_factory
            conn = psycopg2.connect(**kwargs)
            self.logger.info("Database Connected")
            return conn, conn.cursor()
        except Exception as e:
            self.logger.critical('Postgres connection failure: {0}'.format(e))
            raise ('Postgres connection failure: {0}'.format(e))

    def execute(self, sql, data=None):
        if data is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, data)
        try:
            return self.cursor.fetchall()
        except Exception as e:
            return e
