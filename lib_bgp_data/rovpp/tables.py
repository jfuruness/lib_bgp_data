#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROVPP_ASes_Table and Subprefix_Hijack_Temp_Table

These two classes inherits from the Database class. The Database class
does allow for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function, because it would only ever be
used when combining with the roas table, which does a parallel seq_scan,
thus any indexes are not used since they are not efficient. Each table
follows the table name followed by a _Table since it inherits from the
database class.

Possible future improvements:
    -Add test cases
"""

from random import sample
from .enums import Policies, Hijack_Types
from ..utils import Database, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROVPP_ASes_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
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

class ROVPP_MRT_Announcements_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
                 rovpp_mrt_announcements (
                 origin bigint,
                 as_path bigint ARRAY,
                 prefix CIDR
                 );"""
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping ROVPP_MRT_Announcements")
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_mrt_announcements")
        self.logger.debug("ROVPP_MRT_Announcements Table dropped")

    def populate_mrt_announcements(self, subprefix_hijack, hijack_type):
        """Populates the mrt announcements table"""

        sql = """INSERT INTO rovpp_mrt_announcements(
              origin, as_path, prefix) VALUES
              (%s, %s, %s)"""
        attacker_data = [subprefix_hijack["attacker"],
                         [subprefix_hijack["attacker"]],
                         subprefix_hijack["more_specific_prefix"]]
        victim_data = [subprefix_hijack["victim"],
                       [subprefix_hijack["victim"]],
                       subprefix_hijack["expected_prefix"]]
        data_list = [attacker_data]
        if hijack_type != Hijack_Types.NO_COMPETING_ANNOUNCEMENT_HIJACK.value:
            data_list.append(victim_data)
        for data in data_list:
            self.cursor.execute(sql, data)

class Subprefix_Hijack_Temp_Table(Database):
    """Class with database functionality.

    THIS SHOULD BE DELETED LATER AND ADDED INTO BGPSTREAM.COM CLASS!!!
    THIS IS JUST FOR FAKE DATA!!!!

    In depth explanation at the top of the file."""

    __slots__ = []

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        self.clear_table()
        sql = """CREATE UNLOGGED TABLE subprefix_hijack_temp(
                 more_specific_prefix CIDR,
                 attacker bigint,
                 url varchar(200),
                 expected_prefix CIDR,
                 victim bigint
                 );"""
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping Subprefix Hijacks")
        self.cursor.execute("DROP TABLE IF EXISTS subprefix_hijack_temp;")
        self.logger.debug("Subprefix Hijacks Table dropped")

    def populate(self, ases, hijack_type):
        """Populates table with fake data"""

        # Gets two random ases without duplicates
        attacker, victim = sample(ases, k=2)
        sql = """INSERT INTO subprefix_hijack_temp(
              more_specific_prefix, attacker, expected_prefix, victim) VALUES
              (%s, %s, %s, %s)"""
        data = ['1.2.3.0/24',  # more_specfic_prefix
                attacker,  # Random attacker
                '1.2.0.0/16',  # expected_prefix
                victim]
        if hijack_type == Hijack_Types.PREFIX_HIJACK.value:
            data[0] = data[2]
        self.cursor.execute(sql, data)


####################
### Subtables!!! ###
####################

class ROVPP_ASes_Subtable(Database):
    def _create_tables(self):
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS {} (
                 asn bigint,
                 as_type text,
                 impliment BOOLEAN
                 );""".format(self.name)
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.
        Should be called at the start of every run.
        """

        self.logger.debug("Dropping {}".format(self.name))
        self.cursor.execute("DROP TABLE IF EXISTS {}".format(self.name))
        self.logger.debug("{} dropped".format(self.name))

    def set_implimentable_ases(self, percent, attacker):
        """Sets ases to impliment. Due to large sample size,
           1 (the attacker) is not subtracted from the count,
           since we don't know which data set the attacker is from"""

        sql = """UPDATE {0} SET impliment = TRUE
                FROM (SELECT * FROM {0}
                         WHERE {0}.asn != {1}
                         ORDER BY RANDOM() LIMIT (
                             SELECT COUNT(*) FROM {0}) * ({2}::decimal/100.0)
                         ) b
               WHERE b.asn = {0}.asn;""".format(self.name, attacker, percent)
        self.execute(sql)

    def change_routing_policies(self, policy):
        sql = """UPDATE {} SET as_type = {}
                 WHERE impliment = TRUE;""".format(self.name, policy)
        self.execute(sql)

class ROVPP_Top_100_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self):
        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_top_100_ases AS (
                 SELECT a.asn, {} AS as_type, FALSE as impliment
                     FROM rovpp_ases a ORDER BY asn DESC LIMIT 100
                 );""".format(Policies.BGP.value)
        self.cursor.execute(sql)


class ROVPP_Edge_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self):
        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_edge_ases AS (
                     SELECT r.asn, {} AS as_type, FALSE as impliment
                         FROM rovpp_ases r
                         INNER JOIN rovpp_as_connectivity c ON c.asn = r.asn
                     WHERE c.connectivity = 0
                 );""".format(Policies.BGP.value)
        self.cursor.execute(sql)

class ROVPP_Etc_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self, table_names):
        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_etc_ases AS (
                 SELECT ra.asn, {} AS as_type, FALSE as impliment
                     FROM rovpp_ases ra""".format(Policies.BGP.value)
        if len(table_names) > 0:
            for table_name in table_names:
                sql += " LEFT JOIN {0} ON {0}.asn = ra.asn".format(table_name)
            # Gets rid of the last comma
            sql += " WHERE"
            for table_name in table_names:
                sql += " {}.asn IS NULL AND".format(table_name)
            # Gets rid of the last \sAND
            sql = sql[:-4]
        sql += ");"
        self.logger.debug("ETC AS SQL:\n\n{}\n".format(sql))
        self.cursor.execute(sql)
