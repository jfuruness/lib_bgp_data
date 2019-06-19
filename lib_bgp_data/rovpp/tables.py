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
from ..utils import Database, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROVPP_ASes_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger):
        """Initializes the ROVPP ASes table"""

        Database.__init__(self, logger)

    @error_catcher()
    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_ases AS (
                 SELECT customer_as AS asn, 'bgp' AS as_type FROM (
                     SELECT DISTINCT customer_as FROM customer_providers
                     UNION SELECT provider_as FROM customer_providers
                     UNION SELECT peer_as_1 FROM peers
                     UNION SELECT peer_as_2 FROM peers) union_temp
                 );"""
        self.cursor.execute(sql)

    @error_catcher()
    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.info("Dropping ROVPP_ASes")
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_ases")
        self.logger.info("ROVPP_ASes Table dropped")

    @error_catcher()
    def change_routing_policies(self, asns, policy):
        """Changes routing policies to policy for a list of asns"""

        self._create_tables()
        sql = "UPDATE rovpp_ases SET as_type = %s WHERE asn = %s"
        # Should this be a bulk update? Yes. Does it matter? Do it later.
        for asn in asns:
            self.cursor.execute(sql, [policy, asn])

    @error_catcher()
    def get_all(self):
        """Gets everything, for convenience only"""

        return self.execute("SELECT * FROM rovpp_ases;")

class ROVPP_MRT_Announcements_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    @error_catcher()
    def __init__(self, logger):
        """Initializes the ROVPP_MRT_Announcements table"""

        Database.__init__(self, logger)

    @error_catcher()
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

    @error_catcher()
    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.info("Dropping ROVPP_MRT_Announcements")
        self.cursor.execute("DELETE FROM rovpp_mrt_announcements")
        self.logger.info("ROVPP_MRT_Announcements Table dropped")

    @error_catcher()
    def populate_mrt_announcements(self, subprefix_hijack):
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
        for data in [attacker_data, victim_data]:
            self.cursor.execute(sql, data)

class Subprefix_Hijack_Temp_Table(Database):
    """Class with database functionality.

    THIS SHOULD BE DELETED LATER AND ADDED INTO BGPSTREAM.COM CLASS!!!
    THIS IS JUST FOR FAKE DATA!!!!

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger):
        """Initializes the Subprefix_Hijack_Temp_Table"""

        Database.__init__(self, logger)

    @error_catcher()
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

    @error_catcher()
    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.info("Dropping Subprefix Hijacks")
        self.cursor.execute("DROP TABLE IF EXISTS subprefix_hijack_temp;")
        self.logger.info("Subprefix Hijacks Table dropped")

    @error_catcher()
    def populate(self, ases):
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
        self.cursor.execute(sql, data)
