#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables classes to store roas"""

import os
import gzip
from psycopg2.extras import RealDictCursor
from ..logger import error_catcher
from ..database import Database

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
#MAKE VALIDITY TABLE

class Unique_Prefix_Origins_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""

        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

#        return None###########################################################
        if self.test is False:
            sql = """DROP TABLE IF EXISTS unique_prefix_origins;"""
        self.cursor.execute(sql)

    @error_catcher()
    def fill_table(self):
        """Gets all unique Prefix Origins and stores them in a table"""

        sql = """CREATE TABLE unique_prefix_origins AS
                 SELECT DISTINCT as_path[array_upper(as_path, 1)]
                 as origin_as, prefix, 100 as placeholder 
                 FROM mrt_announcements ORDER BY prefix ASC;"""
        self.cursor.execute(sql)

    @error_catcher()
    def write_validator_file(self, path):
        """Takes unique prefix origin table and converts to a csv then gzips"""

        sql = "COPY unique_prefix_origins TO %s DELIMITER '\t';"
        self.cursor.execute(sql, [path])
        self._gzip_file(path)
        self.logger.info("Wrote validator file")
        self.logger.info("Deleted old validator csv")
        return "{}.gz".format(path), self._get_line_count(path)

    @error_catcher()
    def _get_line_count(self, path):
        """returns the line count of a file in python"""

        #https://stackoverflow.com/q/845058/8903959
        with open(path) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    @property
    def name(self):
        """Returns the name of the table"""

        return "unique_prefix_origins"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['prefix', 'origin']

    def _gzip_file(self, path):
        """Gzips the validator.txt file"""

        with open(path, 'rb') as f_in, gzip.open('{}.gz'.format(path), 'wb') as f_out:
            f_out.writelines(f_in)
        self.cursor.execute("SELECT COUNT(1) FROM unique_prefix_origins")
        return self.cursor.fetchone()

    def close(self):
        """Closes the database connection correctly"""

        self.cursor.execute("""DROP TABLE IF EXISTS unique_prefix_origins;""")
        self.cursor.close()
        self.conn.close()

class Validity_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""

        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE TABLE IF NOT EXISTS validity (
                 PRIMARY KEY(asn, prefix),
                 asn bigint,
                 prefix cidr,
                 validity smallint);"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_index(self):
        """Creates index on validity_table"""

        sql = """CREATE INDEX IF NOT EXISTS validity_valid_index ON validity
                  (validity);"""
        self.cursor.execute(sql)


    @property
    def name(self):
        """Returns the name of the table"""

        return "validity"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['asn', 'prefix', 'validity']
