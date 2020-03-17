#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for relationship data tables

The relationship classes inherits from the Generic_Table class. The Generic_Table
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function since this data is only used by
the extrapolator, which does not use indexes. Each table follows the
table name followed by a _Table since it inherits from the Generic_Table
class. In addition, since this data is used for the rovpp simulation,
there are also rovpp tables

There is also the rovpp_as_connectivity_table and the rovpp_asses_table.
The rovpp_as_connectivity_table is generated from the rovpp relationship
tables, and contains info on the connectivity of all ASes. The class
rovpp_ases_table can clear the table it creates at initialization,
fill itself with data from the rovpp_peers and rovpp_customer_providers
table, and has the name and column properties that are used in the
utils function to insert CSVs into the database.
"""

import logging

from ..database import Generic_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def make_sure_tables_exist(table_classes: list):
    """Makes sure tables exist before continuing.

    If they don't runs parser to create them. This is just in
    case certain tables are not filled already like ASes and
    AS_Connectivity need peers and customers
    """

    try:
        for Table_Class in table_classes:
            with Table_Class() as _db:
                assert _db.get_count() > 0
    except AssertionError:
        # Needed here to avoid cirular imports
        from ..relationships_parser import Relationships_Parser
        Relationships_Parser().run()



class Provider_Customers_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "provider_customers"

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS provider_customers (
              provider_as bigint,
              customer_as bigint
              );"""
        self.execute(sql)

class Peers_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "peers"

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS peers (
              peer_as_1 bigint,
              peer_as_2 bigint
              );"""
        self.execute(sql)

class ASes_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "ases"

    def _create_tables(self):
        """Creates tables if they do not exists.

        Called during intialization of the database class.
        """

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS ases (
                 asn bigint,
                 as_type smallint,
                 impliment BOOLEAN
                 );"""
        self.cursor.execute(sql)

    def fill_table(self):
        """Populates the ases table with data from the tables
        peers and provider_customers.
        """


        make_sure_tables_exist([Peers_Table, Provider_Customers_Table])

        self.clear_table()
        logging.debug("Initializing ases table")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS ases AS (
                 SELECT customer_as AS asn, 'bgp' AS as_type,
                    FALSE AS impliment FROM (
                     SELECT DISTINCT customer_as FROM provider_customers
                     UNION SELECT DISTINCT provider_as FROM provider_customers
                     UNION SELECT DISTINCT peer_as_1 FROM peers
                     UNION SELECT DISTINCT peer_as_2 FROM peers) union_temp
                 );"""
        self.execute(sql)


class AS_Connectivity_Table(Generic_Table):
    """Class with database functionality.

    This table contains each ASN and it's associated connectivity.
    Connectivity = # customers + # peers"""

    __slots__ = []

    name = "as_connectivity"

    def fill_table(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        make_sure_tables_exist([ASes_Table])

        # Drops the table if it exists
        self.clear_table()
        # I know there is a better way to do this, but due to this deadline
        # I must press forward. Apologies for the bad code.
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              as_connectivity AS (
              SELECT ases.asn AS asn,
              COALESCE(cp.connectivity, 0) +
                COALESCE(p1.connectivity, 0) +
                COALESCE(p2.connectivity, 0)
                  AS connectivity
              FROM ases
              LEFT JOIN (SELECT cp.provider_as AS asn,
                         COUNT(cp.provider_as) AS connectivity
                         FROM provider_customers cp
                         GROUP BY cp.provider_as) cp
              ON ases.asn = cp.asn
              LEFT JOIN (SELECT p.peer_as_1 AS asn,
                         COUNT(p.peer_as_1) AS connectivity
                         FROM peers p GROUP BY p.peer_as_1) p1
              ON ases.asn = p1.asn
              LEFT JOIN (SELECT p.peer_as_2 AS asn,
                         COUNT(p.peer_as_2) AS connectivity
                         FROM peers p GROUP BY p.peer_as_2) p2
              ON ases.asn = p2.asn
              );"""

        self.execute(sql)
