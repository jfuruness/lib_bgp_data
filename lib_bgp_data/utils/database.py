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
from .logger import error_catcher, Thread_Safe_Logger as Logger

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@contextmanager
def db_connection(table=None,
                  logger=Logger(),
                  clear=False,
                  cursor_factory=RealDictCursor):
    if table:
        t = table(logger, cursor_factory=cursor_factory)
    else:
        t = Database(logger, cursor_factory=cursor_factory)
    if clear:
        t.clear_tables()
        t._create_tables()
    yield t
    t.close()

# Must be done to avoid circular imports
from .config import Config
from .utils import Pool, delete_paths


class Database:
    """Interact with the database"""

    __slots__ = ['logger', 'conn', 'cursor']

    @error_catcher()
    def __init__(self, logger=Logger(), cursor_factory=RealDictCursor):
        """Create a new connection with the database"""

        # Initializes self.logger
        self.logger = logger
        self._connect(cursor_factory)

    @error_catcher()
    def _connect(self, cursor_factory=RealDictCursor, create_tables=True):
        """Connects to db with default RealDictCursor.

        Note that RealDictCursor returns everything as a dictionary."""

        kwargs = Config(self.logger).get_db_creds()
        if cursor_factory:
            kwargs["cursor_factory"] = cursor_factory
        # In case the database is somehow off we wait
        for i in range(10):
            try:
                conn = psycopg2.connect(**kwargs)
                self.logger.debug("Database Connected")
                self.conn = conn
                # Automatically execute queries
                self.conn.autocommit = True
                self.cursor = conn.cursor()
                break
            except:
                time.sleep(10)
        if create_tables:
            # Creates tables if do not exist
            self._create_tables()

    def _create_tables(self):
        """Method that is overwritten when inherited"""

        pass

    def execute(self, sql, data=None):
        """Executes a query. Returns [] if no results."""

        if data is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, data)
        try:
            return self.cursor.fetchall()
        except psycopg2.ProgrammingError:
            self.logger.debug("No results to fetch")
            return []

    def multiprocess_execute(self, sqls):
        """Executes sql statements in parallel"""

        self.close()
        with Pool(self.logger, None, 1, "database execute") as db_pool:
            db_pool.map(lambda self, sql: self._reconnect_execute(sql),
                        [self]*len(sqls),
                        sqls)
        self.__init__(self.logger)

    def _reconnect_execute(self, sql):
        """To be used for parellel queries.

        In parallel queries, one connection between multiple processes
        is not allowed."""

        self.__init__(self.logger)
        self.execute(sql)
        self.close()

    @error_catcher()
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

        self.logger.info("Vacuum analyzing db now")
        self.execute("VACUUM ANALYZE;")
        self.execute("CHECKPOINT;")
        if full:
            self.execute("VACUUM FULL ANALYZE;")

    @error_catcher()
    def unhinge_db(self):
        """Enhances database, but doesn't allow for writing to disk."""

        self.logger.info("unhinging db")
        ram = Config(self.logger).ram
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

        delete_paths(self.logger, "/tmp/db_modify.sql")
        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        self._restart_postgres()
        # Removes sql file to clean up
        os.remove("/tmp/db_modify.sql")
        self.logger.debug("unhinged db")

    @error_catcher()
    def rehinge_db(self):
        """Restores postgres 11 defaults"""


        self.logger.info("rehinging db")
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
        delete_paths(self.logger, "/tmp/db_modify.sql")
        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        self._restart_postgres()
        # Removes sql file to clean up
        os.remove("/tmp/db_modify.sql")
        self.logger.debug("rehinged db")

    @error_catcher()
    def _restart_postgres(self):
        """Restarts postgres and all connections."""

        self.close()
        check_call(Config(self.logger).restart_postgres_cmd, shell=True)
        time.sleep(30)
        self._connect(create_tables=False)

    @error_catcher()
    def get_all(self):
        """Gets all rows from table"""

        return self.execute("SELECT * FROM {}".format(self.name))

    @error_catcher()
    def get_count(self):
        """Gets count from table"""

        sql = "SELECT COUNT(*) FROM {}".format(self.name)
        return self.execute(sql)[0]["count"]

    @property
    def columns(self):
        """Returns the columns of the table

        used in utils to insert csv into the database"""

        sql = """SELECT column_name FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = %s;
              """
        self.cursor.execute(sql, [self.name])
        # Make sure that we don't get the _id columns
        return [x['column_name'] for x in self.cursor.fetchall()
                if "_id" not in x['column_name']]

    @property
    def name(self):
        """Returns the table name

        used in utils to insert csv into the database"""

        # takes out _Table and makes lowercase
        return self.__class__.__name__[:-6].lower()
