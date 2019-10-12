#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_W_ROAs_Table

MRT_W_ROAs_Table inherits from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table. This class does not contain an index creation function, because
that index is never used, and is therefore a waste of time. Each table
follows the table name followed by a _Table since it inherits from the
database class.

Design choices:
    -There is no index creation function since indexes are never used

Possible future improvements:
    -Add test cases
"""

from ..utils import Database, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class MRT_W_Roas_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        self.clear_table()
        self.unhinge_db()
        self.logger.info("Vacuum analyzing tables now that db is unhinged")
        self.execute("VACUUM ANALYZE;")
        self.logger.info("Creating mrt_w_roas")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              mrt_w_roas AS (
              SELECT DISTINCT ON (m.prefix, m.as_path, m.origin)
                  m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN roas r ON m.prefix <<= r.prefix
              );"""
        self.cursor.execute(sql)
        # used in the extrapolator
        self.cursor.execute("CREATE INDEX ON mrt_w_roas USING btree(prefix)")
        self.rehinge_db()
        self.logger.debug("mrt_w_roas created")

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.debug("Dropping MRT_W_Roas")
        self.cursor.execute("DROP TABLE IF EXISTS mrt_w_roas")
        self.logger.debug("MRT_W_Roas table dropped")

class MRT_W_Hijack_Invalid_Prefixes_Table(Database):
    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist

        creates tables of all the invalid or hijacked prefixes"""

        self.clear_table()
        self.unhinge_db()
        self.logger.info("Vacuum analyzing tables now that db is unhinged")
        self.execute("VACUUM ANALYZE")
        self.logger.info("Creating mrt_w_hijack_invalid_prefixes")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              mrt_w_hijack_invalid_prefixes AS (
              SELECT DISTINCT ON (m.prefix, m.as_path, m.origin)
                  m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN hijack_temp h ON h.prefix = m.prefix and h.origin = m.origin
              UNION
              SELECT DISTINCT ON (m.prefix, m.as_path, m.origin)
                  m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m 
                  INNER JOIN rov_validity r ON r.prefix = m.prefix and r.origin = m.origin AND r.validity < 0
              );"""
        self.cursor.execute(sql)
        # used in the extrapolator
        self.cursor.execute("CREATE INDEX ON mrt_w_hijack_invalid_prefixes USING btree(prefix)")
        self.rehinge_db()
        self.logger.debug("mrt_w_hijack_invalid_prefixes created")

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.debug("Dropping MRT_W_Hijack_Invalid_Prefixes")
        self.cursor.execute("DROP TABLE IF EXISTS mrt_w_hijack_invalid_prefixes")
        self.logger.debug("MRT_W_Hijack_Invalid_Prefixes table dropped")

class MRT_W_Hijack_Invalid_Extraprefixes_Table(Database):
    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist

        creates tables of all the invalid or hijacked prefixes"""

        self.clear_table()
        self.unhinge_db()
        self.logger.info("Vacuum analyzing tables now that db is unhinged")
        self.execute("VACUUM ANALYZE")
        self.logger.info("Creating mrt_w_hijack_invalid_superprefixes")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              mrt_w_hijack_invalid_extraprefixes AS (
              SELECT DISTINCT ON (m.prefix, m.as_path, m.origin)
                  m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN hijack_temp h ON h.prefix << m.prefix OR (h.prefix = m.prefix AND h.origin != m.origin)
              UNION

             SELECT DISTINCT ON (m.prefix, m.as_path, m.origin)
                  m.time, m.prefix, m.as_path, m.origin
              FROM mrt_announcements m
                  INNER JOIN rov_validity r ON r.prefix << m.prefix OR (r.prefix = m.prefix AND r.origin != m.origin) AND r.validity >= 0
              );"""
        self.cursor.execute(sql)
        # used in the extrapolator
        self.cursor.execute("CREATE INDEX ON mrt_w_hijack_invalid_extraprefixes USING btree(prefix)")
        self.rehinge_db()
        self.logger.debug("mrt_w_hijack_invalid_extraprefixes created")

    @error_catcher()
    def clear_table(self):
        """Clears the tables. Should be called at the start of every run"""

        self.logger.debug("Dropping MRT_W_Hijack_Invalid_extraPrefixes")
        self.cursor.execute("DROP TABLE IF EXISTS mrt_w_hijack_invalid_extraprefixes")
        self.logger.debug("MRT_W_Hijack_Invalid_extraPrefixes table dropped")
