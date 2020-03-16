#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database and context manager db_connection

The Database class can interact with a database. It can also be
inherited to allow for its functions to be used for specific tables in
the database. Other Table classes inherit the database class to be used
in utils functions that write data to the database. To do this, the
class that inherits the database must be named the table name plus
_Table. For more information on how to do this, see the README on how to
add a submodule.

Fucntionality also exists to be able to unhinge and rehinge the
database. When the database is unhinged, it becomes as optimized as
possible. Checkpointing (writing to disk) is basically disabled, and
must be done manually with checkpoints and db restarts. We use this for
massive table joins that would otherwise take an extremely long amount
of time.

db_connection is used as a context manager to be able to connect to the
database, and have the connection close properly upon leaving.

Design Choices:
-RealDictCursor was used as the default cursor factory so that if table
 columns moved around everything wouldn't break, and using a dictionary
 is very easy
-Unlogged tables used for speed
-Disable corruption safety measures for speed

Possible Future improvements:
-Move unhinge and rehinge db to different sql files."""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
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
from ..utils import utils, config_logging

class Database:
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

        # Gets the global section header to connect to that db
        from .config import global_section_header
        assert global_section_header is not None
        # Database needs access to the section header
        kwargs = Config(global_section_header).get_db_creds()
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
                logging.warning("Couldn't connect to db {e}")
                time.sleep(10)
        if hasattr(self, "_create_tables"):
            # Creates tables if do not exist
            self._create_tables()

    def execute(self, sql: str, data: iter = None) -> list:
        """Executes a query. Returns [] if no results."""

        assert (data is None
                or isinstance(data, list)
                or isinstance(data, tuple)), "Data must be list/tuple"

        if data is None:
            self.cursor.execute(sql)
        else:
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
