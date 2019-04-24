#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from multiprocessing import Process, cpu_count
from .config import Config
from .logger import error_catcher
from .database import Database
from .database import db_connection
from .utils import Pool
from . import utils

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

        return #################################################
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              mrt_w_roas AS (
              SELECT m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN roas r ON m.prefix <<= r.prefix
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        return
        self.logger.info("Dropping MRT_W_Roas")
        self.cursor.execute("DROP TABLE IF EXISTS mrt_w_roas")
        self.logger.info("MRT_W_Roas table dropped")

    def create_index(self):
        """Creates an index"""

        return
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

#        self.clear_table()
#        self._create_tables()
#        self.create_index()
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

        p_ranges = ["{}.0.0.0/3".format(x) for x in range(0, 256, 32)]
        p_ranges.append("255.255.255.255")
        
        table_names = ["mrt_w_roas_contained_or_equal_{}".format(
            x.replace(".", "_").replace("/", "_")) for x in p_ranges]
            
        drop_table_sqls = []
        create_table_sqls = []
        create_index_sqls = []
        add_table_name_sqls = []
        for prefix, table_name in zip(p_ranges, table_names):
            drop_table_sqls.append("DROP TABLE IF EXISTS {}".format(table_name))
            create_table_sql  = "CREATE UNLOGGED TABLE {} AS (".format(table_name)
            create_table_sql += "SELECT * FROM mrt_w_roas WHERE prefix <<= "
            create_table_sql += "'{}');".format(prefix)
            create_table_sqls.append(create_table_sql)
            create_index_sql =  "CREATE INDEX ON {} USING GIST".format(table_name)
            create_index_sql += "(prefix inet_ops, origin);"
            create_index_sqls.append(create_index_sql)
            add_name = "INSERT INTO mrt_w_roas_names VALUES ('{}');".format(
                table_name)
            add_table_name_sqls.append(add_name)

        sqls = [
        """DROP TABLE IF EXISTS mrt_w_roas_names;""",
        """CREATE UNLOGGED TABLE mrt_w_roas_names (name varchar(100));"""]

        for sql in sqls:
            self.cursor.execute(sql)

        with Pool(self.logger, cpu_count()-1, 1, "split") as split_pool:
            drop_old_tables = Process(target=self.drop_mrt_async)
            drop_old_tables.start()
            split_pool.map(self.create_tables,
                           drop_table_sqls,
                           create_table_sqls,
                           create_index_sqls,
                           add_table_name_sqls)
            drop_old_tables.join()
        print("ALL DONE")

    @error_catcher()
    def create_tables(self, drop_table_sqls, create_table, create_index, add_name):
        import sys
        print("Creating a table now")
        sys.stdout.flush()
#        input()
        # Must do this because this is a multiprocessor func
        # So needs multiple db connections
        with db_connection(Database, self.logger) as db:
            print("Database connected")
            for i, sql in enumerate([drop_table_sqls, create_table, create_index, add_name]):
                print("Executing sql statement {}".format(i))
                print(sql)
                sys.stdout.flush()
                db.cursor.execute(sql)

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

    @error_catcher()
    def get_tables(self):
        self.cursor.execute("SELECT * FROM mrt_w_roas_names;")
        return [x.get("name") for x in self.cursor.fetchall()]

class Stubs_Table(Database):
    """Stubs table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS stubs_final (
              asn bigint,
              parent bigint);"""
        self.cursor.execute(sql)

    def generate_stubs_table(self):

        self.logger.info("Generating final stubs table")
        asn_rows = []
        for result in self.execute("SELECT * FROM stubs;"):
            parent = result["parent_asn"]
            while True:
                new_results = self.execute(
                    "SELECT * FROM stubs WHERE stub_asn=%s", [parent])
                if len(new_results) > 0:
                    parent = new_results[0]["parent_asn"]
                else:
                    break
            asn_rows.append([result["stub_asn"], parent])
        self.logger.debug(asn_rows)
        utils.rows_to_db(self.logger, asn_rows, "/tmp/stubs_final.csv", Stubs_Table)
        self.logger.info("Final stubs table generated")
        self.create_index()

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.info("Dropping Stubs final")
        self.cursor.execute("DROP TABLE IF EXISTS stubs_final")
        self.logger.info("Stubs final table dropped")

    def create_index(self):
        """Creates an index"""

        self.logger.info("Creating index")
        sql = """CREATE INDEX IF NOT EXISTS stubs_final_index
                 ON stubs_final(asn);"""
        self.cursor.execute(sql)
        self.logger.info("Index created")

    @property
    def name(self):
        """Returns the name of the table"""

        return "stubs_final"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['asn', 'parent']
