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

from ...utils.database import Generic_Table
from ...utils import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"


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
        from .relationships_parser import Relationships_Parser
        Relationships_Parser().run()


class Provider_Customers_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "provider_customers"
    columns = ["provider_as", "customer_as"]

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
    columns = ["peer_as_1", "peer_as_2"]

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
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name}(
              asn BIGINT,
              as_types BOOLEAN[]);"""
        self.execute(sql)

    def fill_table(self):
        """Populates the ases table with data from the tables
        peers and provider_customers.
        """

        make_sure_tables_exist([Peers_Table, Provider_Customers_Table])

        logging.debug("Initializing ases table")
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS ases AS (
                 SELECT asn AS asn, ARRAY[]::BOOLEAN[] AS as_types FROM (
                     SELECT DISTINCT customer_as AS asn FROM provider_customers
                     UNION SELECT DISTINCT provider_as AS asn FROM provider_customers
                     UNION SELECT DISTINCT peer_as_1 AS asn FROM peers
                     UNION SELECT DISTINCT peer_as_2 AS asn FROM peers) union_temp
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
              --COALESCE(pc.connectivity, 0) +
                COALESCE(p1.connectivity, 0) +
                COALESCE(p2.connectivity, 0)
                  AS connectivity
              FROM ases
              LEFT JOIN (SELECT cp.customer_as AS asn,
                         COUNT(cp.customer_as) AS connectivity
                         FROM provider_customers cp
                         GROUP BY cp.customer_as) pc
              ON ases.asn = pc.asn
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

class Relationships_Table(Generic_Table):
    name = "as_data"
    columns = ["asn", "peers", "customers", "providers", "stubs", "stub",
                "multihomed", "as_type"]

    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name}(
              asn BIGINT,
              peers BIGINT[],
              customers BIGINT[],
              providers BIGINT[],
              stubs BIGINT[],
              stub BOOLEAN,
              multihomed BOOLEAN,
              as_type SMALLINT);"""
        self.execute(sql)


    def fill_table(self):
        class AS:
            def __init__(self, asn):
                self.asn = asn
                self.peers = set()
                self.customers = set()
                self.providers = set()
                self.as_type = 0

            @property
            def db_row(self):
                def asns(as_objs: list):
                    return "{" + ",".join(str(x.asn) for x in as_objs) + "}"

                return [self.asn,
                        asns(self.peers),
                        asns(self.customers),
                        asns(self.providers),
                        asns(self.stubs),
                        self.stub,
                        self.multihomed,
                        self.as_type]

            @property
            def stub(self):
                if len(self.peers) == 0 and len(self.customers) == 0:
                    return True
                else:
                    return False

            @property
            def multihomed(self):
                if len(self.providers) > 1 and self.stub:
                    return True
                else:
                    return False

            @property
            def stubs(self):
                return [x for x in self.customers if x.stub]

        with ASes_Table() as db:
            ases_rows = db.get_all()

        with Peers_Table() as db:
            peers_rows = db.get_all()

        with Provider_Customers_Table() as db:
            provider_customers_rows = db.get_all()

        ases = set([x["asn"] for x in ases_rows])
        ases = {x: AS(x) for x in ases}
        for peer_row in peers_rows:
            p1, p2 = (peer_row["peer_as_1"], peer_row["peer_as_2"])
            ases[p1].peers.add(ases[p2])
            ases[p2].peers.add(ases[p1])

        for provider_customers_row in provider_customers_rows:
            customer = provider_customers_row["customer_as"]
            provider = provider_customers_row["provider_as"]
            ases[customer].providers.add(ases[provider])
            ases[provider].customers.add(ases[customer])

        rows = [x.db_row for x in ases.values()]
        utils.rows_to_db(rows, "/tmp/relationship.csv", Relationships_Table)
