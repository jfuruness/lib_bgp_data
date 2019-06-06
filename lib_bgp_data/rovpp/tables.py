#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ROVPP_ASes_Table

ROVPP_Ases_Table inherits from the Database class. The Database class
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
        self.cursor.execute("DELETE FROM rovpp_ases")
        self.logger.info("ROVPP_ASes Table dropped")

    @error_catcher()
    def change_routing_policies(self, asns, policy):
        """Changes routing policies to policy for a list of asns"""

        sql = "UPDATE rovpp_ases SET as_type = %s WHERE asn = %s"
        # Should this be a bulk update? Yes. Does it matter? No.
        for asn in asns:
            self.cursor.execute(sql, [policy, asn])

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
                        list(subprefix_hijack["attacker"]),
                        subprefix_hijack["more_specific_prefix"]]
        victim_data = [subprefix_hijack["victim"],
                        list(subprefix_hijack["victim"]),
                        subprefix_hijack["expected_prefix"]]
        for data in [attacker_data, victim_data]:
            self.cursor.execute(sql, data)

