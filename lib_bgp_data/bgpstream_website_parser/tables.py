#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains numerous bgpstream.com tables

These tables must all inherit from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. Each table
follows the table name followed by a _Table since it inherits from the
database class. These tables also contain functions that delete
duplicates, format tables for IPV4 or IPV6 data, and can create
subtables that are subsets of the data

Design choices:
    -Indexes are created on the times for the what if analysis
    -The main tables are never deleted to never get rid of website data

Possible future improvements:
    -Add test cases
"""

from psycopg2.extras import RealDictCursor
from time import strftime, gmtime
from ..utils import Database, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Hijack_Table(Database):
    """Hijack table class, inherits from database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS hijack (
              hijack_id serial PRIMARY KEY,
              country varchar (50),
              detected_as_path bigint ARRAY,
              detected_by_bgpmon_peers integer,
              detected_origin_name varchar (200),
              detected_origin_number bigint,
              start_time timestamp with time zone,
              end_time timestamp with time zone,
              event_number integer,
              event_type varchar (50),
              expected_origin_name varchar (200),
              expected_origin_number bigint,
              expected_prefix cidr,
              more_specific_prefix cidr,
              url varchar (250)
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_index(self):
        """Creates an index on the times for later table creations"""

        sql = """CREATE INDEX IF NOT EXISTS hijack_index ON hijack
                  USING BTREE(start_time, end_time);"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_temp_table(self, start, end):
        """Creates a hijack table for all hijacks within a time frame.

        Also creates a subprefix hijack table, used in rovpp sims.
        """

        if None in [start, end]:
            self.logger.debug("Not creating temporary tables")
            return

        self.logger.debug("About to create temporary hijack table")
        self.logger.debug("About to drop hijack temp")
        self.cursor.execute("DROP TABLE IF EXISTS hijack_temp;")
        self.logger.debug("Dropped hijack temp")

        # Converts epoch times to utc
        start = strftime('%Y-%m-%d %H:%M:%S', gmtime(start))
        end = strftime('%Y-%m-%d %H:%M:%S', gmtime(end))

        # Create table for all hijacks that overlap with the time frame
        sql = """CREATE UNLOGGED TABLE hijack_temp AS
                    (SELECT h.more_specific_prefix AS prefix,
                    h.detected_origin_number AS origin,
                    h.start_time,
                    COALESCE(h.end_time, now()) AS end_time,
                    h.url,
                    h.expected_prefix,
                    h.expected_origin_number
              FROM hijack h
              WHERE
                (h.start_time, COALESCE(h.end_time, now())) OVERLAPS
                (%s::timestamp with time zone, %s::timestamp with time zone)
              );"""
        self.cursor.execute(sql, [start, end])

        # Creates indexes on the hijack temp table for what if analysis
        sqls = ["""CREATE INDEX ON hijack_temp
                USING GIST (prefix inet_ops, origin);""",
                "CREATE INDEX ON hijack_temp USING GIST (prefix inet_ops);"]
        for sql in sqls:
            self.cursor.execute(sql)
        self.logger.info("Created temporary hijack table")

        # Gets all subprefix hijacks
        self._create_subprefix_hijack_table()

    @error_catcher()
    def _create_subprefix_hijack_table(self):
        """Creates a subprefix hijack tablei. Used in ROVPP sims."""

        # This will get all of the subprefix hijackings within the temp table
        self.cursor.execute("DROP TABLE IF EXISTS subprefix_hijack_temp ;")
        sql = """CREATE UNLOGGED TABLE subprefix_hijack_temp AS
                    (SELECT h.prefix AS more_specific_prefix,
                    h.origin AS attacker,
                    h.url,
                    h.expected_prefix,
                    h.expected_origin_number AS victim
                FROM hijack_temp h
                WHERE h.prefix << h.expected_prefix
                );"""
        self.cursor.execute(sql)
        self.logger.info("Created subprefix hijack table")

    @error_catcher()
    def delete_duplicates(self):
        """Deletes all duplicates from the table."""

        self.logger.info("About to delete duplicates in hijack")
        sql = """DELETE FROM hijack a USING hijack b
              WHERE a.hijack_id < b.hijack_id
              AND a.event_number = b.event_number
              ;"""
        self.cursor.execute(sql)
        self.logger.debug("Duplicates deleted in hijack")

    @error_catcher()
    def filter(self, IPV4=True, IPV6=False):
        """Filters by IPV4 and IPV6."""

        if not IPV6:
            sql = "DELETE FROM hijack WHERE family(expected_prefix) = 6;"
            self.cursor.execute(sql)
        if not IPV4:
            sql = "DELETE FROM hijack WHERE family(expected_prefix) = 4;"
            self.cursor.execute(sql)
        self.logger.debug("Filtered by IPV4 and IPV6")


class Leak_Table(Database):
    """Leak Table class, inherits from Database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist."""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS Leak (
              leak_id serial PRIMARY KEY,
              country varchar (50),
              detected_by_bgpmon_peers integer,
              start_time timestamp with time zone,
              end_time timestamp with time zone,
              event_number integer,
              event_type varchar (50),
              example_as_path bigint ARRAY,
              leaked_prefix cidr,
              leaked_to_name varchar (200) ARRAY,
              leaked_to_number bigint ARRAY,
              leaker_as_name varchar (200),
              leaker_as_number bigint,
              origin_as_name varchar (200),
              origin_as_number bigint,
              url varchar (250)
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Deletes all duplicates from the table."""

        self.logger.info("About to delete duplicates from leak")
        sql = """DELETE FROM leak a USING leak b
              WHERE a.leak_id < b.leak_id AND a.event_number = b.event_number
              ;"""
        self.cursor.execute(sql)
        self.logger.debug("Deleted duplicates from leak")

    @error_catcher()
    def filter(self, IPV4=True, IPV6=False):
        """Filters by IPV4 and IPV6"""

        if not IPV6:
            sql = "DELETE FROM leak WHERE family(leaked_prefix) = 6;"
            self.cursor.execute(sql)
        if not IPV4:
            sql = "DELETE FROM leak WHERE family(leaked_prefix) = 4;"
            self.cursor.execute(sql)
        self.logger.debug("Filtered by IPV4 and IPV6")

    @error_catcher()
    def create_index(self):
        """Creates indexes on the table for later use."""

        sql = """CREATE INDEX IF NOT EXISTS leak_index ON leak
                  USING BTREE(start_time, end_time);"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_temp_table(self, start, end):
        """We don't deal with this data yet."""

        pass  # Unnessecary at this time


class Outage_Table(Database):
    """Outage Table class, inherits from Database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS outage (
              outage_id serial PRIMARY KEY,
              as_name varchar (200),
              as_number bigint,
              country varchar (25),
              start_time timestamp with time zone,
              end_time timestamp with time zone,
              event_number integer,
              event_type varchar (25),
              number_prefixes_affected integer,
              percent_prefixes_affected smallint,
              url varchar(150)
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Deletes all duplicates from the table"""

        self.logger.info("About to delete duplicates from outage")
        sql = """DELETE FROM outage a USING outage b
              WHERE a.outage_id < b.outage_id
              AND a.event_number = b.event_number
              ;"""
        self.cursor.execute(sql)
        self.logger.debug("Deleted duplicates from outage")

    @error_catcher()
    def filter(self, IPV4=True, IPV6=False):
        """This function is called, but ASes don't have prefixes"""

        pass

    @error_catcher()
    def create_index(self):
        """Creates index for later use."""

        sql = """CREATE INDEX IF NOT EXISTS outage_index ON outage
                  USING BTREE(start_time, end_time);"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_temp_table(self, start, end):
        """We don't deal with this data yet."""

        pass  # unnessecary at this time
