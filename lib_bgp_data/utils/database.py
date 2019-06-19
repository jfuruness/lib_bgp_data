#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

# Due to circular imports this must be here
from contextlib import contextmanager

@contextmanager
def db_connection(table, logger):
    t = table(logger)
    yield t
    t.close()

import psycopg2
from psycopg2.extras import RealDictCursor
from .config import Config
from .logger import error_catcher
from .utils import Pool

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

    @property
    def columns(self):
        """Returns the columns of the table

        used in utils to insert csv into the database"""

        sql = """SELECT column_name FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = %s;
              """
        self.cursor.execute(sql, [self.name])
        return [x['column_name'] for x in self.cursor.fetchall()]

    @property
    def name(self):
        """Returns the table name

        used in utils to insert csv into the database"""

        # takes out _Table and makes lowercase
        return self.__class__.__name__[:-6].lower()
