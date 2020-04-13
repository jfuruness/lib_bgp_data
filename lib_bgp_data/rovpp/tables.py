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
from .enums import Policies, Attack_Types
from .enums import AS_Types, Data_Plane_Conditions as Conds
from .enums import Control_Plane_Conditions as C_Plane_Conds
from ..database import Database, Generic_Table
from ..mrt_parser.tables import MRT_Announcements_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Attackers_Table(MRT_Announcements_Table):

    name = "attackers"

class Victims_Table(MRT_Announcements_Table):

    name = "victims"

#################
### Subtables ###
#################

class ASes_Subtable(Database):

    def set_adopting_ases(self, percent, attacker, deterministic):
        """Sets ases to impliment"""

        ases = set([x["asn"] for x in self.Input_Table.get_all()])
        if attacker in ases:
            ases.remove(attacker)
        ases_to_set = len(ases) * percent // 100

        assert ases_to_set > 0, "ASes to set is 0?? Can't be right"

        if deterministic:
            ases = list(ases)
            ases.sort()
            adopting_ases = sample(ases, k=ases_to_set)
            percent_s_str = " OR asn = ".join("%s" for AS in adopting_ases)
            sql = """UPDATE {self.name} SET adopting = TRUE
                  WHERE asn = {percent_s_str}"""
            self.execute(sql, adopting_ases)
        else:
            sql = """UPDATE {0} SET adopting = TRUE
                    FROM (SELECT * FROM {0}
                             WHERE {0}.asn != {1}
                             ORDER BY RANDOM() LIMIT {2}
                             ) b
                   WHERE b.asn = {0}.asn
                   ;""".format(self.name, attacker, ases_to_set)
            self.execute(sql)

    def change_routing_policies(self, policy):
        sql = """UPDATE {self.name} SET as_type = {policy}
                 WHERE adopting = TRUE;"""
        self.execute(sql)

class Subtable_Rib_Out(Generic_Table):

    def fill_table(self):
        sql = f"""CREATE UNLOGGED TABLES IF NOT EXISTS {self.name} AS (
              SELECT * FROM {ROVPP_Extrapolator_Rib_out_Table.name} a
              INNER JOIN {self.input_name} b
                ON a.asn = b.asn;"""
        self.execute(sql)

class Top_100_ASes_Table(ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "top_100_ases"

    @property
    def Rib_Out_Table(self):
        return Top_100_ASes_Rib_Out_Table

    def fill_table(self, *args):

        ases = [3356, 1299, 174, 2914, 3257, 6762, 6939, 6453, 3491, 6461,
                1273, 3549, 9002, 5511, 12956, 4637, 7473, 209, 12389, 701,
                3320, 7018, 7922, 20485, 3216, 9498, 31133, 20764, 6830, 1239,
                52320, 16735, 2828, 15412, 8359, 286, 58453, 28917, 262589,
                10429, 4809, 7738, 4755, 41095, 37468, 33891, 43531, 4766,
                11537, 8220, 31500, 4826, 18881, 7843, 29076, 4230, 46887,
                34800, 62663, 8167, 9304, 7029, 5588, 267613, 3303, 11164,
                20804, 8218, 5617, 4134, 1221, 7474, 13786, 22773, 9049, 28329,
                12741, 61832, 28598, 132602, 3326, 22356, 2516, 7545, 26615,
                6663, 2497, 577, 23520, 55410, 9318, 3786, 20115, 3267, 3223,
                20562, 6128, 3741, 9505, 50607]

        ases_str = " OR asn = ".join(ases)
        # TODO deadlines so fuck it
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                 SELECT a.asn,
                    {Policies.DEFAULT.value} AS as_type,
                    FALSE as adopting
                FROM {ASes_Table.name} a WHERE asn = {ases_str}
                 );"""              
        self.cursor.execute(sql)

class Top_100_ASes_Rib_Out_Table(Top_100_ASes_Table, Subtable_Rib_Out):
    name = "top_100_ases_rib_out"


class Edge_ASes_Table(ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "edge_ases"

    @property
    def Rib_Out_Table(self):
        return Edge_ASes_Rib_Out_Table

    def fill_table(self, *args):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS edge_ases AS (
                     SELECT r.asn,
                        {Policies.DEFAULT.value} AS as_type,
                        FALSE as adopting
                         FROM {ASes_Table.name} r
                         INNER JOIN {AS_Connectivity_Table.name} c
                            ON c.asn = r.asn
                     WHERE c.connectivity = 0
                 );"""
        self.execute(sql)

class Edge_ASes_Rib_Out_Table(Edge_ASes_Table, Subtable_Rib_Out):
    name = "edge_ases_rib_out"


class Etc_ASes_Table(ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "etc_ases"

    @property
    def Rib_Out_Table(self):
        return Etc_ASes_Rib_Out_Table

    def fill_table(self, table_names):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                 SELECT ra.asn,
                    {Policies.DEFAULT.value} AS as_type,
                    FALSE as adopting
                     FROM {ASes_Table.name} ra"""
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
        logging.debug("ETC AS SQL:\n\n{sql}\n")
        self.execute(sql)

class Etc_ASes_Rib_Out_Table(Etc_ASes_Table, Subtable_Rib_Out):
    name = "etc_ases_rib_out"

class Simulation_Results_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    name = "simulation_results"

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
                 simulation_results (
                 attack_type text,
                 subtable_name text,
                 attacker_asn bigint,
                 attacker_prefix CIDR,
                 victim bigint,
                 victim_prefix CIDR,
                 adopt_pol text,
                 percent bigint,
                 trace_hijacked_collateral bigint,
                 trace_nothijacked_collateral bigint,
                 trace_blackholed_collateral bigint,
                 trace_total_collateral bigint,
                 trace_hijacked_adopting bigint,
                 trace_nothijacked_adopting bigint,
                 trace_blackholed_adopting bigint,
                 trace_preventivehijacked_adopting bigint,
                 trace_preventivenothijacked_adopting bigint,
                 trace_total_adopting bigint,
                 c_plane_has_attacker_prefix_origin_collateral bigint,
                 c_plane_has_only_victim_prefix_origin_collateral bigint,
                 c_plane_has_bhole_collateral bigint,
                 no_rib_collateral bigint,
                 c_plane_has_attacker_prefix_origin_adopting bigint,
                 c_plane_has_only_victim_prefix_origin_adopting bigint,
                 c_plane_has_bhole_adopting bigint,
                 no_rib_adopting bigint
                 );"""
        self.execute(sql)

    def insert(self,
               subtable_name,
               hijack,
               hijack_type,
               adopt_pol_name,
               percent,
               traceback_data,
               c_plane_data):

        sql = f"""INSERT INTO {self.name}(
                 hijack_type,
                 subtable_name,
                 attacker_asn,
                 attacker_prefix,
                 victim,
                 victim_prefix,
                 adopt_pol,
                 trial_num,
                 percent_iter,
                 trace_hijacked_collateral,
                 trace_nothijacked_collateral,
                 trace_blackholed_collateral,
                 trace_total_collateral,
                 trace_hijacked_adopting,
                 trace_nothijacked_adopting,
                 trace_blackholed_adopting,
                 trace_total_adopting,
                 c_plane_has_attacker_prefix_origin_collateral,
                 c_plane_has_only_victim_prefix_origin_collateral,
                 c_plane_has_bhole_collateral,
                 no_rib_collateral,
                 c_plane_has_attacker_prefix_origin_adopting,
                 c_plane_has_only_victim_prefix_origin_adopting,
                 c_plane_has_bhole_adopting,
                 no_rib_adopting)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s);"""

        1/0 # These need updating, dicts are different now

        data = [hijack_type,
                subtable_name,
                hijack.attacker_asn,
                hijack.attacker_prefix,
                hijack.victim_asn,
                hijack.victim_prefix,
                adopt_pol_name,
                percent,

                traceback_data[Conds.HIJACKED.value][AS_Types.NON_ADOPTING.value],
                traceback_data[Conds.NOTHIJACKED.value][AS_Types.NON_ADOPTING.value],
                traceback_data[Conds.BHOLED.value][AS_Types.NON_ADOPTING.value],
                int(sum(v[AS_Types.NON_ADOPTING.value] for k, v in traceback_data.items())) + c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.NO_RIB.value],

                traceback_data[Conds.HIJACKED.value][AS_Types.ADOPTING.value],
                traceback_data[Conds.NOTHIJACKED.value][AS_Types.ADOPTING.value],
                traceback_data[Conds.BHOLED.value][AS_Types.ADOPTING.value],
                int(sum(v[AS_Types.ADOPTING.value] for k, v in traceback_data.items())) + c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.NO_RIB.value],

                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.RECEIVED_BHOLE.value],
                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.NO_RIB.value],

                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.RECEIVED_BHOLE.value],
                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.NO_RIB.value]]
        self.execute(sql, data)
