#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables classes to store roas"""

import os
import gzip
from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
#MAKE VALIDITY TABLE

class Unique_Prefix_Origins_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor):
        """Initializes the announcement table"""

        Database.__init__(self, logger, cursor_factory)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.logger.debug("Dropping unique prefix origin table")
        self.cursor.execute("DROP TABLE IF EXISTS unique_prefix_origins")
        self.logger.debug("Dropped unique prefix origin table")
        self.logger.info("Creating unique prefix origings table")
        sql = """CREATE UNLOGGED TABLE unique_prefix_origins AS
                 SELECT DISTINCT origin, prefix, 100 as placeholder 
                 FROM mrt_w_roas ORDER BY prefix ASC;"""
        self.cursor.execute(sql)
        self.logger.info("Created unique prefix origins table")

    @error_catcher()
    def write_validator_file(self, path):
        """Takes unique prefix origin table and converts to a csv then gzips"""

        self.logger.debug("About to create file for validator")
        sql = "COPY unique_prefix_origins TO %s DELIMITER '\t';"
        self.cursor.execute(sql, [path])
        self._gzip_file(path)
        self.logger.debug("Wrote validator file")
        self.logger.debug("Deleted old validator csv")
        return "{}.gz".format(path), self._get_line_count(path)

    @error_catcher()
    def _get_line_count(self, path):
        """returns the line count of a file in python"""

        #https://stackoverflow.com/q/845058/8903959
        with open(path) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    def _gzip_file(self, path):
        """Gzips the validator.txt file"""

        with open(path, 'rb') as f_in, gzip.open('{}.gz'.format(path), 'wb') as f_out:
            f_out.writelines(f_in)
        return self.execute("SELECT COUNT(*) FROM unique_prefix_origins")[0]


class ROV_Validity_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor):
        """Initializes the announcement table"""

        Database.__init__(self, logger, cursor_factory)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.execute("DROP TABLE IF EXISTS rov_validity")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rov_validity (
                 asn bigint,
                 prefix cidr,
                 validity smallint);"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        self.execute("DROP TABLE IF EXISTS rov_validity")

    @error_catcher()
    def create_index(self):
        """Creates index on validity_table"""

        sql = """CREATE INDEX IF NOT EXISTS rov_validity_valid_index ON validity
                  (validity);"""
        self.cursor.execute(sql)
