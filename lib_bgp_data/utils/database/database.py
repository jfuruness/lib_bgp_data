#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database. See README for in depth details"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import logging
from multiprocessing import cpu_count
import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import Config
from . import config
from .postgres import Postgres

from ..logger import config_logging
from .. import utils


class Database(Postgres):
    """Interact with the database"""

    __slots__ = ['conn', 'cursor', '_clear']

    def __init__(self, cursor_factory=RealDictCursor, clear=False):
        """Create a new connection with the database"""

        # Initializes self.logger
        config_logging()
        self._connect(cursor_factory)
        self._clear = clear

    def __enter__(self):
        """This allows this class to be used as a context manager

        With this you don't need to worry about closing connections.
        """

        # Checks if it has attributes, because this parent class does not
        # Only the generic table has these attributes
        # If clear is set clear the table
        if self._clear and hasattr(self, "clear_table"):
            self.clear_table()
        # Create the tables if possible
        if hasattr(self, "_create_tables"):
            self._create_tables()
        return self

    def __exit__(self, type, value, traceback):
        """Closes connection, exits contextmanager"""

        self.close()
        
    def _connect(self, cursor_factory=RealDictCursor):
        """Connects to db with default RealDictCursor.

        Note that RealDictCursor returns everything as a dictionary."""

        # Database needs access to the section header
        kwargs = Config().get_db_creds()
        if cursor_factory:
            kwargs["cursor_factory"] = cursor_factory
        # In case the database is somehow off we wait
        for i in range(10):
            try:
                conn = psycopg2.connect(**kwargs)

                logging.debug("Database Connected")
                self.conn = conn
                # Automatically execute queries
                self.conn.autocommit = True
                self.cursor = conn.cursor()
                break
            except psycopg2.OperationalError as e:
                logging.warning(f"Couldn't connect to db {e}")
                time.sleep(10)
        if hasattr(self, "_create_tables"):
            # Creates tables if do not exist
            self._create_tables()

    def execute(self, sql: str, data: iter = []) -> list:
        """Executes a query. Returns [] if no results."""

        assert (isinstance(data, list)
                or isinstance(data, tuple)), "Data must be list/tuple"

        self.cursor.execute(sql, data)

        try:
            return self.cursor.fetchall()
        except psycopg2.ProgrammingError as e:
            return []

    def multiprocess_execute(self, sqls: list):
        """Executes sql statements in parallel"""

        # Must close so connection isn't duplicated
        self.close()
        with utils.Pool(None, 1, "database execute") as db_pool:
            db_pool.map(lambda self, sql: self._reconnect_execute(sql),
                        [self]*len(sqls),
                        sqls)
        self.__init__()

    def _reconnect_execute(self, sql: str):
        """To be used for parellel queries.

        In parallel queries, one connection between multiple processes
        is not allowed.
        """

        # Connect to db
        self.__init__()
        # Execute sql
        self.execute(sql)
        # Close db
        self.close()

    def close(self):
        """Closes the database connection correctly"""

        self.cursor.close()
        self.conn.close()

    def vacuum_analyze_checkpoint(self, full=False):
        """Vaccums, analyzes, and checkpoints.

        Vacuum saves space and improves efficiency.
        Analyze creates statistics on tables for better query planning.
        Checkpoint writes memory to disk.
        A full vacuum rewrites entire db to save space.
        """

        logging.info("Vacuum analyzing db now")
        self.execute("VACUUM ANALYZE;")
        self.execute("CHECKPOINT;")
        if full:
            self.execute("VACUUM FULL ANALYZE;")
