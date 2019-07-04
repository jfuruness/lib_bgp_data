#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

# Due to circular imports this must be here
from contextlib import contextmanager
from .logger import Thread_Safe_Logger as Logger

@contextmanager
def db_connection(table, logger=None):
    if not logger:
        logger = Logger()
    t = table(logger)
    yield t
    t.close()

import psycopg2
from psycopg2.extras import RealDictCursor
from multiprocessing import cpu_count
from subprocess import check_call
import os
from .config import Config
from .logger import error_catcher
from .utils import Pool
from .config import Config

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Database:
    """Interact with the database"""

    __slots__ = ['logger', 'conn', 'cursor']

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor):
        """Create a new connection with the databse"""

        # Initializes self.logger
        self.logger = logger
        self._connect(cursor_factory)

    @error_catcher()
    def _connect(self, cursor_factory):
        """Connects to db"""

        kwargs = Config(self.logger).get_db_creds()
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
            return {}

    def multiprocess_execute(self, sqls):
        """Executes sql statements in parallel"""

        self.close()
        with Pool(self.logger, None, 1, "database execute") as db_pool:
            db_pool.map(lambda self, sql: self._reconnect_execute(sql),
                        [self]*len(sqls),
                        sqls)
        self.__init__(self.logger)

    def _reconnect_execute(self, sql):
        self.__init__(self.logger)
        self.execute(sql)

    @error_catcher()
    def close(self):
        """Closes the database connection correctly"""

        self.cursor.close()
        self.conn.close()

    def vacuum(self):
        """Vaccums db for efficiency"""

        self.cursor.execute("VACUUM")

    @error_catcher()
    def unhinge_db(self):
        ram = Config(self.logger).ram
        # This will make it so that your database never writes to
        # disk unless you tell it to. It's faster, but harder to use
        sqls = [# https://www.2ndquadrant.com/en/blog/
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

        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        # SHOULD BE MOVED TO CONF!!! LET USER SET THEIR OWN CMD!!!
        check_call(Config(self.logger).restart_postgres_cmd, shell=True)
        time.sleep(10)
        # Removes sql file to clean up
        os.remove("/tmp/db_modify.sql")

    @error_catcher()
    def rehinge_db(self):
        """Restores postgres 11 defaults"""

        ram = Config(self.logger).ram
        # This will make it so that your database never writes to
        # disk unless you tell it to. It's faster, but harder to use
        sqls = [# https://www.2ndquadrant.com/en/blog/
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

        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        # SHOULD BE MOVED TO CONF!!! LET USER SET THEIR OWN CMD!!!
        check_call(Config(self.logger).restart_postgres_cmd, shell=True)
        time.sleep(10)
        # Removes sql file to clean up
        os.remove("/tmp/db_modify.sql")

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
