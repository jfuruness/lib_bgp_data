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

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging
from time import strftime, gmtime

from ..database import Generic_Table


class Data_Table(Generic_Table):
    """Data table class, inherits from database.

    This is supposed to have general functions for other
    bgpstream.com tables.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []


    def create_index(self):
        """Creates an index on the times for later table creations"""

        sql = f"""CREATE INDEX IF NOT EXISTS {self.name}_index ON {self.name}
                USING BTREE(start_time, end_time);"""
        self.execute(sql)

    def delete_duplicates(self):
        """Deletes all duplicates from the table."""

        logging.debug(f"About to delete duplicates in {self.name}")
        sql = f"""DELETE FROM {self.name} a USING {self.name} b
              WHERE a.id < b.id
              AND a.event_number = b.event_number
              ;"""
        logging.debug(sql)
        self.execute(sql)
        logging.debug(f"Duplicates deleted in {self.name}")


class Hijacks_Table(Data_Table):
    """Hijack table class, inherits from database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = "hijacks"
    prefix_column = "expected_prefix"

    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS hijacks (
              id serial PRIMARY KEY,
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

    
class Leaks_Table(Data_Table):
    """Leak Table class, inherits from Database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = "leaks"    
    prefix_column = "leaked_prefix"

    def _create_tables(self):
        """Creates tables if they do not exist."""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS leaks (
              id serial PRIMARY KEY,
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

class Outages_Table(Data_Table):
    """Outage Table class, inherits from Database.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = "outages"
    
    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS outages (
              id serial PRIMARY KEY,
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
