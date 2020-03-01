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

# Due to circular imports this must be here
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from multiprocessing import cpu_count
from subprocess import check_call
import os
import time
from ..utils import Config, utils, config_logging


__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Database:
    """Interact with the database"""

    __slots__ = ['conn', 'cursor', 'clear']

    # NOTE: SHOULD INHERIT DECOMETA HERE!!!

    
    def __init__(self, cursor_factory=RealDictCursor, clear=False):
        """Create a new connection with the database"""

        # Initializes self.logger
        config_logging()
        self._connect(cursor_factory)
        self.clear=clear

    def __enter__(self):
        if self.clear and type(self) != Database:
            self.clear_table()
            if hasattr(self, "_create_tables"):
                self._create_tables()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        
    def _connect(self, cursor_factory=RealDictCursor):
        """Connects to db with default RealDictCursor.

        Note that RealDictCursor returns everything as a dictionary."""

        from .config import global_section_header
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
            except:
                time.sleep(10)
        if hasattr(self, "_create_tables"):
            # Creates tables if do not exist
            self._create_tables()

    def execute(self, sql, data=None):
        """Executes a query. Returns [] if no results."""

        assert isinstance(data, list) or isinstance(data, tuple), "Data must be list/tuple"
        if data is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, data)
        try:
            return self.cursor.fetchall()
        except psycopg2.ProgrammingError as e:
            logging.debug(f"No results to fetch: {e}")
            return []

    def multiprocess_execute(self, sqls):
        """Executes sql statements in parallel"""

        self.close()
        with utils.Pool(None, 1, "database execute") as db_pool:
            db_pool.map(lambda self, sql: self._reconnect_execute(sql),
                        [self]*len(sqls),
                        sqls)
        self.__init__()

    def _reconnect_execute(self, sql):
        """To be used for parellel queries.

        In parallel queries, one connection between multiple processes
        is not allowed."""

        self.__init__(logging)
        self.execute(sql)
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

    def unhinge_db(self):
        """Enhances database, but doesn't allow for writing to disk."""

        logging.info("unhinging db")
        # access to section header
        ram = Config(global_section_header).ram
        # This will make it so that your database never writes to
        # disk unless you tell it to. It's faster, but harder to use
        sqls = [  # https://www.2ndquadrant.com/en/blog/
                # basics-of-tuning-checkpoints/
                # manually do all checkpoints to abuse this thing
                "ALTER SYSTEM SET checkpoint_timeout TO '1d';",
                "ALTER SYSTEM SET checkpoint_completion_target TO .9;",
                # The amount of ram that needs to be hit before a write do disk
                "ALTER SYSTEM SET max_wal_size TO '{}MB';".format(ram-1000),
                # Disable autovaccum
                "ALTER SYSTEM SET autovacuum TO off;",
                # Change max number of workers
                # Since this is now manual it can be higher
                "ALTER SYSTEM SET autovacuum_max_workers TO {};".format(
                    cpu_count() - 1),
                # Change the number of max_parallel_maintenance_workers
                # Since its manual it can be higher
                "ALTER SYSTEM SET max_parallel_maintenance_workers TO {};"\
                    .format(cpu_count() - 1),
                "ALTER SYSTEM SET maintenance_work_mem TO '{}MB';".format(
                    int(ram/5))]

        utils.delete_paths("/tmp/db_modify.sql")
        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        self._restart_postgres()
        # Removes sql file to clean up
        os.remove("/tmp/db_modify.sql")
        logging.debug("unhinged db")

    def rehinge_db(self):
        """Restores postgres 11 defaults"""


        logging.info("rehinging db")
        # This will make it so that your database never writes to
        # disk unless you tell it to. It's faster, but harder to use
        sqls = [  # https://www.2ndquadrant.com/en/blog/
                # basics-of-tuning-checkpoints/
                # manually do all checkpoints to abuse this thing
                "ALTER SYSTEM SET checkpoint_timeout TO '5min';",
                "ALTER SYSTEM SET checkpoint_completion_target TO .5;",
                # The amount of ram that needs to be hit before a write do disk
                "ALTER SYSTEM SET max_wal_size TO '1GB';",
                # Disable autovaccum
                "ALTER SYSTEM SET autovacuum TO ON;",
                # Change max number of workers
                # Since this is now manual it can be higher
                "ALTER SYSTEM SET autovacuum_max_workers TO 3;",
                # Change the number of max_parallel_maintenance_workers
                # Since its manual it can be higher
                "ALTER SYSTEM SET max_parallel_maintenance_workers TO 2;",
                "ALTER SYSTEM SET maintenance_work_mem TO '64MB';"]
        utils.delete_paths("/tmp/db_modify.sql")
        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        self._restart_postgres()
        # Removes sql file to clean up
        os.remove("/tmp/db_modify.sql")
        logging.debug("rehinged db")

    def _restart_postgres(self):
        """Restarts postgres and all connections."""

        self.close()
        # access to section header
        check_call(Config(global_section_header).restart_postgres_cmd,
                   shell=True)
        time.sleep(30)
        self._connect(create_tables=False)
