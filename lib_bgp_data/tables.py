#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from ..config import Config
from ..logger import error_catcher
from ..database import Database
from ..database import db_connection
from pathos import pool as Pool

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Announcements_Covered_By_Roas_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS mrt_w_roas AS (
              SELECT m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN roas r ON m.prefix << r.prefix
              ) TABLESPACE ram;"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Dropping MRT_W_Roas")
        self.cursor.execute("DROP TABLE mrt_w_roas")
        self.logger.info("MRT_W_Roas table dropped")

    def create_index(self):
        """Creates an index"""

        self.logger.info("Creating index")
        sql = """CREATE INDEX IF NOT EXISTS mrt_w_roas_index
                 ON mrt_w_roas USING GIST (prefix inet_ops);"""
        self.cursor.execute(sql)
        self.logger.info("Index created")

    @property
    def name(self):
        """Returns the name of the table"""

        return "mrt_w_roas"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['time', 'prefix', 'as_path', 'origin']

    @error_catcher()
    def join_mrt_with_roas(self):
        """Joins the mrt table with the roas table

        Joins the mrt with the roas table. Both are in ram.
        The resulting table will also be in ram. Then the
        mrt and roas tables are dropped.
        """

        self.clear_Table()
        self.create_tables()
        self.create_index()
        # Splits the tables, drops the old tables
        self.split_tables()

    @error_catcher()
    def split_tables(self):
        """Splits the table by prefix for input to the extrapolator

        The extrapolator extrapolates by prefix. In this step we will
        split the tables based on prefix and return a list of tables.
        Then the old tables will be dropped, and the database will be
        vaccumed
        """

        create_table_sql  = "CREATE TABLE {} AS (".format(table_name)
        create_table_sql += "SELECT * FROM mrt_w_roas WHERE prefix <<= "
        create_table_sql += "{}) TABLESPACE RAM;".format(prefix)

        p_ranges = ["{}.0.0.0/5".format(x) for x in range(0, 256, 8)]
        p_ranges.append("255.255.255.255")
        
        table_names = ["mrt_w_roas_contained_or_equal_{}".format(
            x.replace(".", "_").replace("/", "_") for x in p_ranges]
            
        create_table_sqls = []
        create_index_sqls = []
        add_table_name_sqls = []
        for prefix, table_name in zip(prepends, table_names):
            create_table_sql  = "CREATE TABLE {} AS (".format(table_name)
            create_table_sql += "SELECT * FROM mrt_w_roas WHERE prefix <<= "
            create_table_sql += "{}) TABLESPACE RAM;".format(prefix)
            create_table_sqls.append(create_table_sql)
            create_index_sql =  "CREATE INDEX ON {} USING GIST".format(table_name)
            create_index_sql += "(prefix inet_ops, origin)"
            create_index_sqls.append(create_index_sql)
            add_name = "INSERT INTO mrt_w_roas_names VALUES ({});".format(
                table_name)
            add_table_name_sqls.append(add_name)

        sqls = [
        """DROP TABLE IF EXISTS mrt_w_roas_names;""",
        """CREATE TABLE mrt_w_roas_names (name varchar(100));"""]

        for sql in sqls:
            self.cursor.execute(sql)

        with Pool(self.logger, cpu_count()-1, 1, "split_pool") as split_pool:
            drop_old_tables = Process(target=drop_mrt_async)
            drop_old_tables.start()
            split_pool.map(create_tables,
                           create_table_sqls,
                           create_index_sqls,
                           add_table_name_sqls)
            self.cursor.execute("DROP TABLE mrt_w_roas;")
            drop_old_tables.join()

    @error_catcher()
    def create_tables(self, create_table, create_index, add_name):
        for sql in [create_table, create_index, add_name]:
            self.cursor.execute(sql)

    @error_catcher()
    def drop_mrt_async(self):
        """Function that drops the mrt table to be called in multiprocess"""

        with db_connection(MRT_Announcements, self.logger) as mrt_table:
            mrt_table.cursor.execute("DROP TABLE mrt_announcements;")
            mrt_table.cursor.execute("DROP TABLE roas;")
            mrt_table.cursor.execute("VACUUM;")

    @error_catcher()
    def get_tables(self):
        self.cursor.execute("SELECT * FROM mrt_w_roas_names;")
