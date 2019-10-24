#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for relationship data tables

The relationship classes inherits from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function since this data is only used by
the extrapolator, which does not use indexes. Each table follows the
table name followed by a _Table since it inherits from the Database
class. In addition, since this data is used for the rovpp simulation,
there are also rovpp tables

There is also the rovpp_as_connectivity_table and the rovpp_asses_table. 
The rovpp_as_connectivity_table is generated from the rovpp relationship
tables, and contains info on the connectivity of all ASes. The class
rovpp_ases_table can clear the table it creates at initialization, 
fill itself with data from the rovpp_peers and rovpp_customer_providers
table, and has the name and column properties that are used in the 
utils function to insert CSVs into the database.

Design choices:
    -There is no index creation function since indexes are never used
     for the typical purpose of the relationship data

Possible future improvements:
    -Add test cases
    -The data is actualy provider customers, change the name to
     provider_customers in this file and all others
"""

from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Customer_Providers_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS {};".format(self.name))
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS {} (
              provider_as bigint,
              customer_as bigint
              );""".format(self.name)
        self.cursor.execute(sql)


class Peers_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS {};".format(self.name))
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS {} (
              peer_as_1 bigint,
              peer_as_2 bigint
              );""".format(self.name)
        self.cursor.execute(sql)


class ROVPP_Customer_Providers_Table(Customer_Providers_Table):
    """Class with database functionality. self.name overridden

    In depth explanation at the top of the file."""

    __slots__ = []

    pass


class ROVPP_Peers_Table(Peers_Table):
    """Class with database functionality. self.name overridden

    In depth explanation at the top of the file."""

    __slots__ = []

    pass


class ROVPP_ASes_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""
    
    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exists.
    
        Called during intialization of the database class.
        """
    
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_ases (
                 asn bigint,
                 as_type smallint,
                 impliment BOOLEAN
                 );"""
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping ROVPP_ASes")
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_ases")
        self.logger.debug("ROVPP_ASes Table dropped")

    def fill_table(self):
        """Populates the rovpp_ases table with data from the tables
        rovpp_peers and rovpp_customer_providers.
        """
        self.clear_table()
        self.logger.debug("Initializing rovpp_as_table")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_ases AS (
                 SELECT customer_as AS asn, 'bgp' AS as_type, FALSE AS impliment FROM (
                     SELECT DISTINCT customer_as FROM rovpp_customer_providers
                     UNION SELECT provider_as FROM rovpp_customer_providers
                     UNION SELECT peer_as_1 FROM rovpp_peers
                     UNION SELECT peer_as_2 FROM rovpp_peers) union_temp
                 );"""
        self.cursor.execute(sql)
    

class ROVPP_AS_Connectivity_Table(Database):
    """Class with database functionality.

    This table contains each ASN and it's associated connectivity.
    Connectivity = # customers + # peers"""

    __slots__ = []

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class."""

        # Drops the table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_as_connectivity;")
        # I know there is a better way to do this, but due to this deadline
        # I must press forward. Apologies for the bad code.
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
              rovpp_as_connectivity AS (
              SELECT ases.asn AS asn,
              COALESCE(cp.connectivity, 0) +
                COALESCE(p1.connectivity, 0) +
                COALESCE(p2.connectivity, 0)
                  AS connectivity
              FROM rovpp_ases ases
              LEFT JOIN (SELECT cp.provider_as AS asn,
                         COUNT(cp.provider_as) AS connectivity
                         FROM rovpp_customer_providers cp
                         GROUP BY cp.provider_as) cp
              ON ases.asn = cp.asn
              LEFT JOIN (SELECT p.peer_as_1 AS asn,
                         COUNT(p.peer_as_1) AS connectivity
                         FROM rovpp_peers p GROUP BY p.peer_as_1) p1
              ON ases.asn = p1.asn
              LEFT JOIN (SELECT p.peer_as_2 AS asn,
                         COUNT(p.peer_as_2) AS connectivity
                         FROM rovpp_peers p GROUP BY p.peer_as_2) p2
              ON ases.asn = p2.asn
              );"""

        self.cursor.execute(sql)

    @error_catcher()
    def get_ases_by_transitivity(self):
        sql = """SELECT * FROM rovpp_as_connectivity
              WHERE connectivity = 0;"""
        non_transit_ases = [x["asn"] for x in self.execute(sql)]
        sql = """SELECT * FROM rovpp_as_connectivity
              WHERE connectivity > 0;"""
        transit_ases = [x["asn"] for x in self.execute(sql)]
        return transit_ases, non_transit_ases

    @error_catcher()
    def get_top_100_ases(self):
        sql = """SELECT * FROM rovpp_as_connectivity
              ORDER BY connectivity DESC LIMIT 100;"""
        return [x["asn"] for x in self.execute(sql)]

    @error_catcher()
    def get_not_top_100_ases(self):
        sql = """SELECT * FROM rovpp_as_connectivity
              ORDER BY connectivity DESC OFFSET 100;"""
        return [x["asn"] for x in self.execute(sql)]
