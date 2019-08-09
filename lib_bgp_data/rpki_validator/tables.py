#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains tables for the RPKI Validator to run.

These tables both do inherit from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function, because it is never used. Each
table follows the table name followed by a _Table since it inherits from
the database class.

In addition, the Unique Prefix Origin Table takes the unique prefix
origins from the MRT announcements table. Then it copies this into a file
and gzips it for use by the RPKI Validator. This gzipped file contains a
placeholder of 100 because the RPKI Validator doesn't observe prefix
origins that are not seen by less than 5 peers.

Design choices:
    -We serve our own file for the RPKI Validator to be able to use
     old prefix origin pairs
    -The gzipped prefix origin file contains a placeholder of 100 because
     the RPKI Validator will not use any prefix origin pairs that are
     seen by less than 5 peers.
    -There is no index creation function since indexes are never used
    -This table is usually only combined with the roas table, for which
     it uses a parallel seq_scan, with no indexes
Possible future improvements:
    -Add test cases
"""


import gzip
from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Unique_Prefix_Origins_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist."""

        self.logger.debug("Dropping unique prefix origin table")
        self.cursor.execute("DROP TABLE IF EXISTS unique_prefix_origins")
        self.logger.debug("Dropped unique prefix origin table")
        self.logger.info("Creating unique prefix origins table")
        sql = """CREATE UNLOGGED TABLE unique_prefix_origins AS
                 SELECT DISTINCT origin, prefix, 100 as placeholder
                 FROM mrt_w_roas ORDER BY prefix ASC;"""
        self.cursor.execute(sql)
        self.logger.debug("Created unique prefix origins table")

    @error_catcher()
    def write_validator_file(self, path):
        """Takes unique prefix origin table and converts to a csv.gz."""

        self.logger.info("About to create file for validator")
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

    @error_catcher()
    def _gzip_file(self, path):
        """Gzips the validator.txt file"""

        with open(path, 'rb') as f_in, gzip.open('{}.gz'.format(path),
                                                 'wb') as f_out:
            f_out.writelines(f_in)


class ROV_Validity_Table(Database):
    """ROV Validity Table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor):
        """Initializes the ROV Validity table"""

        Database.__init__(self, logger, cursor_factory)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rov_validity (
                 origin bigint,
                 prefix cidr,
                 validity smallint);"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        self.execute("DROP TABLE IF EXISTS rov_validity")
