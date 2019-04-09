#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import Config
from .logger import error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@contextmanager
def db_connection(table, self.logger):
    t = table(self.logger)
    yield t
    t.close()

class Database:
    """Interact with the database"""

    __slots__ = ['logger', 'config', 'conn', 'cursor', 'test']

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Create a new connection with the databse"""

        # Initializes self.logger
        self.logger = logger
        self.config = Config(self.logger)
        self.test = test
        self._connect(cursor_factory)

    @error_catcher()
    def _connect(self, cursor_factory):
        """Connects to db"""

        kwargs = self.config.get_db_creds()
        if cursor_factory:
            kwargs["cursor_factory"] = cursor_factory
        conn = psycopg2.connect(**kwargs)
        self.logger.info("Database Connected")
        self.conn = conn
        self.conn.autocommit = True
        self.cursor = conn.cursor()
        # Creates tables if do not exist
        self._create_tables()

    def _create_tables(self):
        """Method that is overwritten when inherited"""

        pass

    @error_catcher()
    def execute(self, sql, data=None):
        """Executes a query"""

        if data is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, data)
        try:
            return self.cursor.fetchall()
        except psycopg2.ProgrammingError:
            self.logger.warning("No results to fetch")
            return None

    @error_catcher()
    def close(self):
        """Closes the database connection correctly"""

        # If testing delete test table
        if self.test:
            self._drop_tables()
        self.cursor.close()
        self.conn.close()

    def vacuum(self):
        """Vaccums db for efficiency"""

        self.cursor.execute("VACUUM")
