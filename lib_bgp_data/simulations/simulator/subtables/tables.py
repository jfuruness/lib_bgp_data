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

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from ...enums import Policies

from ....utils.database import Generic_Table
from ....collectors.as_rank_website.tables import AS_Rank_Table
from ....collectors.relationships.tables import AS_Connectivity_Table
from ....collectors.relationships.tables import ASes_Table
from ....extrapolator import Simulation_Extrapolator_Forwarding_Table

#################
### Subtables ###
#################


class ASes_Subtable(Generic_Table):
    """Ases subtable (generic type of subtable)"""

    def set_adopting_ases(self, percent, attack, random_seed):
        """Sets ases to impliment"""

        attacker = attack.attacker
        ases = set([x["asn"] for x in self.get_all()])
        # The attacker cannot adopt
        if attacker in ases:
            ases.remove(attacker)
        # Number of adopting ases
        ases_to_set = len(ases) * percent // 100

        # I don't agree with this way of coding it, but this came from up above
        if percent == 0:
            if "edge" in self.name:
                ases_to_set = 1
            else:
                ases_to_set = 0
        if percent == 100:
            ases_to_set -= 1

        if ases_to_set == 0:
            return

        if random_seed:
            self.execute(f"SELECT setseed({random_seed});")

        sql = """UPDATE {0} SET impliment = TRUE
                FROM (SELECT * FROM {0}
                         WHERE {0}.asn != {1}
                         ORDER BY RANDOM() LIMIT {2}
                         ) b
               WHERE b.asn = {0}.asn
               ;""".format(self.name, attacker, ases_to_set)
        self.execute(sql)

    def change_routing_policies(self, policy):
        """Change the adopting ases routing policies"""

        sql = f"""UPDATE {self.name} SET as_type = {policy.value}
                 WHERE impliment = TRUE;"""
        self.execute(sql)


class Subtable_Forwarding_Table(Generic_Table):
    """The forwarding table for whatever subtable."""

    def fill_forwarding_table(self, round_num):
        with Simulation_Extrapolator_Forwarding_Table(round_num=round_num) as _db:
            sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                  SELECT a.asn, a.prefix, a.origin, a.received_from_asn,
                    b.as_type, b.impliment
                    FROM {_db.name} a
                  INNER JOIN {self.input_name} b
                    ON a.asn = b.asn);"""
            self.execute(sql)


class Top_100_ASes_Table(ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "top_100_ases"

    @property
    def Forwarding_Table(self):
        return Top_100_ASes_Forwarding_Table

    def fill_table(self, *args):

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                 SELECT a.asn,
                    {Policies.DEFAULT.value} AS as_type,
                    FALSE as impliment
                FROM {ASes_Table.name} a
                INNER JOIN {AS_Rank_Table.name} b
                    ON b.asn = a.asn
                WHERE b.as_rank <= 100
                 );"""
        self.cursor.execute(sql)


class Top_100_ASes_Forwarding_Table(Top_100_ASes_Table,
                                    Subtable_Forwarding_Table):
    name = "top_100_ases_forwarding"


class Edge_ASes_Table(ASes_Subtable):
    """Subtable that consists of only edge ases
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "edge_ases"

    @property
    def Forwarding_Table(self):
        return Edge_ASes_Forwarding_Table

    def fill_table(self, *args):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS edge_ases AS (
                     SELECT r.asn,
                        {Policies.DEFAULT.value} AS as_type,
                        FALSE as impliment
                         FROM {ASes_Table.name} r
                         INNER JOIN {AS_Connectivity_Table.name} c
                            ON c.asn = r.asn
                     WHERE c.connectivity = 0
                 );"""
        self.execute(sql)


class Edge_ASes_Forwarding_Table(Edge_ASes_Table,
                                 Subtable_Forwarding_Table):
    name = "edge_ases_forwarding"


class Etc_ASes_Table(ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "etc_ases"

    @property
    def Forwarding_Table(self):
        return Etc_ASes_Forwarding_Table

    def fill_table(self, table_names):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                 SELECT ra.asn,
                    {Policies.DEFAULT.value} AS as_type,
                    FALSE as impliment
                     FROM {ASes_Table.name} ra"""
        table_names = [x for x in table_names if x != self.name]
        if len(table_names) > 0:
            for table_name in table_names:
                sql += " LEFT JOIN {0} ON {0}.asn = ra.asn".format(table_name)
            # Gets rid of the last comma
            sql += " WHERE"
            for table_name in table_names:
                sql += f" {table_name}.asn IS NULL AND"
            # Gets rid of the last \sAND
            sql = sql[:-4]
        sql += ");"
        logging.debug(f"ETC AS SQL:\n\n{sql}\n")
        self.execute(sql)


class Etc_ASes_Forwarding_Table(Etc_ASes_Table,
                                Subtable_Forwarding_Table):
    name = "etc_ases_forwarding"
