#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Database that interacts with a database"""

import psycopg2
from psycopg2.extras import RealDictCursor
from ..config import Config
from ..logger import error_catcher
from ..database import Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Hijack_Table(Database):
    """Hijack table class, inherits from database"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the Hijack table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS hijack (
                  hijack_id serial PRIMARY KEY,
                  country varchar (50),
                  detected_as_path bigint ARRAY,
                  detected_by_bgpmon_peers integer,
                  detected_origin_name varchar (200),
                  detected_origin_number bigint,
                  start_time timestamp,
                  end_time timestamp,
                  event_number integer,
                  event_type varchar (50),
                  expected_origin_name varchar (200),
                  expected_origin_number bigint,
                  expected_prefix cidr,
                  more_specific_prefix cidr,
                  url varchar (250)
                  );"""
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_hijack (
              test_hijack_id serial PRIMARY KEY,
              random_num int
              );"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_index(self):
        sql = """CREATE INDEX IF NOT EXISTS hijack_index ON hijack
                 USING GIST(more_specific_prefix inet_ops, detected_origin_number)"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Drops all duplicates from the table"""

        self.logger.info("About to delete duplicates in hijack")
        sql = """DELETE FROM hijack a USING hijack b
              WHERE a.hijack_id < b.hijack_id
              AND a.event_number = b.event_number
              ;"""
        self.cursor.execute(sql)
        self.logger.info("Duplicates deleted in hijack")

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ["country",
                "detected_as_path",
                "detected_by_bgpmon_peers",
                "detected_origin_name",
                "detected_origin_number",
                "start_time",
                "end_time",
                "event_number",
                "event_type",
                "expected_origin_name",
                "expected_origin_number",
                "expected_prefix",
                "more_specific_prefix",
                "url"
                ]

    @property
    def name(self):
        """Returns the table name"""

        return "hijack"


class Leak_Table(Database):
    """Leak Table class, inherits from Database"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the leak table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS Leak (
                  leak_id serial PRIMARY KEY,
                  country varchar (50),
                  detected_by_bgpmon_peers integer,
                  start_time timestamp,
                  end_time timestamp,
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
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_leak (
                  test_leak_id serial PRIMARY KEY,
                  random_num int
                  );"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Drops all duplicates from the table"""

        self.logger.info("About to delete duplicates from leak")
        sql = """DELETE FROM leak a USING leak b
              WHERE a.leak_id < b.leak_id AND a.event_number = b.event_number
              ;"""
        self.cursor.execute(sql)
        self.logger.info("Deleted duplicates from leak")

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ["country",
                "detected_by_bgpmon_peers",
                "start_time",
                "end_time",
                "event_number",
                "event_type",
                "example_as_path",
                "leaked_prefix",
                "leaked_to_name",
                "leaked_to_number",
                "leaker_as_name",
                "leaker_as_number",
                "origin_as_name",
                "origin_as_number",
                "url"
                ]

    @property
    def name(self):
        """Returns the table name"""

        return "leak"

class Outage_Table(Database):
    """Outage Table class, inherits from Database"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the outage table"""
        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist"""

        if self.test is False:
            sql = """CREATE TABLE IF NOT EXISTS outage (
                  outage_id serial PRIMARY KEY,
                  as_name varchar (200),
                  as_number bigint,
                  country varchar (25),
                  start_time timestamp,
                  end_time timestamp,
                  event_number integer,
                  event_type varchar (25),
                  number_prefixes_affected integer,
                  percent_prefixes_affected smallint,
                  url varchar(150)
                  );"""
        else:
            sql = """CREATE TABLE IF NOT EXISTS test_outage (
                  test_leak_id serial PRIMARY KEY,
                  random_num int
                  );"""
        self.cursor.execute(sql)

    @error_catcher()
    def delete_duplicates(self):
        """Drops all duplicates from the table"""

        self.logger.info("About to delete duplicates from outage")
        sql = """DELETE FROM outage a USING outage b
              WHERE a.outage_id < b.outage_id AND a.event_number = b.event_number
              ;"""
        self.cursor.execute(sql)
        self.logger.info("Deleted duplicates from outage")

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ["as_name",
                "as_number",
                "country",
                "start_time",
                "end_time",
                "event_number",
                "event_type",
                "number_prefixes_affected",
                "percent_prefixes_affected",
                "url"
                 ]

    @property
    def name(self):
        """Returns the table name"""

        return "outage"
