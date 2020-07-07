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
from random import sample

from .enums import Non_Default_Policies, Policies, Attack_Types
from .enums import AS_Types, Data_Plane_Conditions as DP_Conds
from .enums import Control_Plane_Conditions as CP_Conds

from ..database import Database, Generic_Table
from ..mrt_parser.tables import MRT_Announcements_Table
from ..relationships_parser.tables import AS_Connectivity_Table, ASes_Table
# Done this way to avoid circular imports

class Attackers_Table(MRT_Announcements_Table):
    """Attackers table that contains the attackers announcements"""

    name = "attackers"

class Victims_Table(MRT_Announcements_Table):
    """Victims table that contains the victims announcements"""

    name = "victims"

# Fix this later
from ..extrapolator_parser.tables import ROVPP_Extrapolator_Rib_Out_Table

#################
### Subtables ###
#################

class ASes_Subtable(Generic_Table):
    """Ases subtable (generic type of subtable)"""

    def set_adopting_ases(self, percent, attacker, deterministic):
        """Sets ases to impliment"""

        ases = set([x["asn"] for x in self.get_all()])
        # The attacker cannot adopt
        if attacker in ases:
            ases.remove(attacker)
        # Number of adopting ases
        ases_to_set = len(ases) * percent // 100

        # Again this is bad code, and bad simulation practice,
        # but it's what Amir wants
        if percent == 0:
            if "edge" in self.name:
                ases_to_set = 1
            else:
                ases_to_set = 0
        if percent == 100:
            ases_to_set -= 1


        if percent > 0:
            assert ases_to_set > 0, f"{percent}|{len(ases)}|{self.name}"
        if ases_to_set == 0:
            return

        # Using seeded randomness
        # NOTE: this should be changed. SQL can use a seed.
        # Updates ases to be adopting
        if deterministic:
            ases = list(ases)
            ases.sort()
            adopting_ases = sample(ases, k=ases_to_set)
            percent_s_str = " OR asn = ".join("%s" for AS in adopting_ases)
            sql = """UPDATE {self.name} SET impliment = TRUE
                  WHERE asn = {percent_s_str}"""
            self.execute(sql, adopting_ases)
        else:
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

class Subtable_Rib_Out(Generic_Table):
    """The rib out table for whatever subtable. Rib out from the extrapolator"""

    def fill_rib_out_table(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
              SELECT a.asn, a.prefix, a.origin, a.received_from_asn,
                b.as_type, b.impliment
                FROM {ROVPP_Extrapolator_Rib_Out_Table.name} a
              INNER JOIN {self.input_name} b
                ON a.asn = b.asn);"""
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

        ases_str = " OR asn = ".join([str(x) for x in ases])
        # TODO deadlines so fuck it
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                 SELECT a.asn,
                    {Policies.DEFAULT.value} AS as_type,
                    FALSE as impliment
                FROM {ASes_Table.name} a WHERE asn = {ases_str}
                 );"""              
        self.cursor.execute(sql)


class Top_100_ASes_Rib_Out_Table(Top_100_ASes_Table, Subtable_Rib_Out):
    name = "top_100_ases_rib_out"


class Edge_ASes_Table(ASes_Subtable):
    """Subtable that consists of only edge ases
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
                        FALSE as impliment
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

class Etc_ASes_Rib_Out_Table(Etc_ASes_Table, Subtable_Rib_Out):
    name = "etc_ases_rib_out"

class Simulation_Results_Table(Database):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    name = "simulation_results"

    """This is kept as one massive table even though it should prob b 3
    the reason being because we run these trials over vms
    so to keep track of indexes across all vms so that none are ever the
    same is unnessecary work. Maybe later we can fix it.
    """

    def _create_tables(self):
        """Creates tables if they do not exist.
        Called during initialization of the database class.
        """

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS
                 {self.name} (
                 attack_type text,
                 subtable_name text,
                 attacker_asn bigint,
                 attacker_prefix CIDR,
                 victim bigint,
                 victim_prefix CIDR,
                 adopt_pol text,
                 percent bigint,
                 percent_iter bigint,
                 trace_hijacked_collateral bigint,
                 trace_nothijacked_collateral bigint,
                 trace_blackholed_collateral bigint,
                 trace_total_collateral bigint,
                 trace_hijacked_adopting bigint,
                 trace_nothijacked_adopting bigint,
                 trace_blackholed_adopting bigint,
                 trace_total_adopting bigint,
                 c_plane_has_attacker_prefix_origin_collateral bigint,
                 c_plane_has_only_victim_prefix_origin_collateral bigint,
                 c_plane_has_bhole_collateral bigint,
                 no_rib_collateral bigint,
                 c_plane_has_attacker_prefix_origin_adopting bigint,
                 c_plane_has_only_victim_prefix_origin_adopting bigint,
                 c_plane_has_bhole_adopting bigint,
                 no_rib_adopting bigint,
                 visible_hijacks_adopting bigint,
                 visible_hijacks_collateral bigint
                 );"""
        self.execute(sql)

    def insert(self,
               subtable_name,
               hijack,
               hijack_type,
               adopt_pol_name,
               percent,
               percent_iter,
               traceback_data,
               c_plane_data,
               visible_hijack_data):

        sql = f"""INSERT INTO {self.name}(
                 attack_type,
                 subtable_name,
                 attacker_asn,
                 attacker_prefix,
                 victim,
                 victim_prefix,
                 adopt_pol,
                 percent,
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
                 no_rib_adopting,
                 visible_hijacks_adopting,
                 visible_hijacks_collateral)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s);"""

        # Also write out cp = control plane dp = dataplane everywhere
        # Had to do it, things where so insanely long unreadable

        # Splits dicts up for readability
        traceback_non_adopting = {k: type_dict[AS_Types.COLLATERAL.value]
                                  for k, type_dict in traceback_data.items()}
        traceback_adopting = {k: type_dict[AS_Types.ADOPTING.value]
                              for k, type_dict in traceback_data.items()}
        cp_non_adopting = {k: type_dict[AS_Types.COLLATERAL.value]
                           for k, type_dict in c_plane_data.items()}
        cp_adopting = {k: type_dict[AS_Types.ADOPTING.value]
                       for k, type_dict in c_plane_data.items()}

        # Calculates totals for readability
        total_traceback_non_adopting = sum(traceback_non_adopting.values())
        total_traceback_non_adopting += cp_non_adopting[CP_Conds.NO_RIB.value]

        total_traceback_adopting = sum(traceback_adopting.values())
        total_traceback_adopting += cp_adopting[CP_Conds.NO_RIB.value]

        test_info = [hijack_type.value,
                     subtable_name,
                     hijack.attacker_asn,
                     hijack.attacker_prefix,
                     hijack.victim_asn,
                     hijack.victim_prefix,
                     Non_Default_Policies(adopt_pol_name).name,
                     percent,
                     percent_iter]

        trace_info = [
            traceback_non_adopting[DP_Conds.HIJACKED.value],
            traceback_non_adopting[DP_Conds.NOTHIJACKED.value],
            traceback_non_adopting[DP_Conds.BHOLED.value],
            total_traceback_non_adopting,

            traceback_adopting[DP_Conds.HIJACKED.value],
            traceback_adopting[DP_Conds.NOTHIJACKED.value],
            traceback_adopting[DP_Conds.BHOLED.value],
            total_traceback_adopting]

        cplane_info = [
            cp_non_adopting[CP_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
            cp_non_adopting[CP_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
            cp_non_adopting[CP_Conds.RECEIVED_BHOLE.value],
            cp_non_adopting[CP_Conds.NO_RIB.value],

            cp_adopting[CP_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
            cp_adopting[CP_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
            cp_adopting[CP_Conds.RECEIVED_BHOLE.value],
            cp_adopting[CP_Conds.NO_RIB.value]]

        v_hjack_info = [visible_hijack_data[x] for x in 
                               [AS_Types.ADOPTING, AS_Types.COLLATERAL]]

        self.execute(sql, test_info + trace_info + cplane_info + v_hjack_info)

class Simulation_Results_Agg_Table(Generic_Table):
    """Table used to aggregate the results for graphing"""

    name = "simulation_results_agg"

    def fill_table(self):
        sql = f""" 
        CREATE UNLOGGED TABLE {self.name} AS (
            SELECT
        
                attack_type, subtable_name, adopt_pol, percent,
        
                --adopting traceback
                trace_hijacked_adopting::decimal / trace_total_adopting::decimal AS trace_hijacked_adopting,
                (trace_blackholed_adopting::decimal + no_rib_adopting::decimal)::decimal / trace_total_adopting::decimal AS trace_disconnected_adopting,
                trace_nothijacked_adopting::decimal / trace_total_adopting::decimal AS trace_connected_adopting,
        
                --collateral traceback
                trace_hijacked_collateral::decimal / trace_total_collateral::decimal AS trace_hijacked_collateral,
                (trace_blackholed_collateral::decimal + no_rib_collateral::decimal)::decimal / trace_total_collateral::decimal AS trace_disconnected_collateral,
                trace_nothijacked_collateral::decimal / trace_total_collateral::decimal AS trace_connected_collateral,
        
                --adopting control plane
                c_plane_has_attacker_prefix_origin_adopting::decimal / trace_total_adopting::decimal AS c_plane_hijacked_adopting,
                (c_plane_has_bhole_adopting::decimal + no_rib_adopting::decimal)::decimal / trace_total_adopting::decimal AS c_plane_disconnected_adopting,
                c_plane_has_only_victim_prefix_origin_adopting::decimal / trace_total_adopting::decimal AS c_plane_connected_adopting,
        
                --collateral control plane
                c_plane_has_attacker_prefix_origin_collateral::decimal / trace_total_collateral::decimal AS c_plane_hijacked_collateral,
                (c_plane_has_bhole_collateral::decimal + no_rib_collateral::decimal)::decimal / trace_total_collateral::decimal AS c_plane_disconnected_collateral,
                c_plane_has_only_victim_prefix_origin_collateral::decimal / trace_total_collateral::decimal AS c_plane_connected_collateral,
        
                --adopting hidden hijacks
                visible_hijacks_adopting::decimal / trace_total_adopting::decimal AS visible_hijacks_adopting,
                (trace_hijacked_adopting::decimal - visible_hijacks_adopting::decimal)::decimal / trace_total_adopting::decimal AS hidden_hijacks_adopting,
        
                --collateral hidden hijacks
                visible_hijacks_collateral::decimal / trace_total_collateral::decimal AS visible_hijacks_collateral,
                (trace_hijacked_collateral::decimal - visible_hijacks_collateral::decimal)::decimal / trace_total_collateral::decimal AS hidden_hijacks_collateral
        
            FROM {Simulation_Results_Table.name}
            WHERE trace_total_adopting > 0 AND trace_total_collateral > 0
        );"""
        self.execute(sql) 

class Simulation_Results_Avg_Table(Generic_Table):
    """Table used to get the confidence intervals for graphing"""

    name = "simulation_results_avg"

    def fill_table(self):
        sql = f"""
        CREATE UNLOGGED TABLE {self.name} AS (
            SELECT
                attack_type, subtable_name, adopt_pol, percent,
        
                --adopting traceback
                AVG(trace_hijacked_adopting) AS trace_hijacked_adopting,
                (1.645 * 2.0 * STDDEV(trace_hijacked_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_adopting_confidence,
                AVG(trace_disconnected_adopting) AS trace_disconnected_adopting,
                (1.645 * 2.0 * STDDEV(trace_disconnected_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_adopting_confidence,
                AVG(trace_connected_adopting) AS trace_connected_adopting,
                (1.645 * 2.0 * STDDEV(trace_connected_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_adopting_confidence,
                --collateral traceback
                AVG(trace_hijacked_collateral) AS trace_hijacked_collateral,
                (1.645 * 2.0 * STDDEV(trace_hijacked_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_collateral_confidence,
                AVG(trace_disconnected_collateral) AS trace_disconnected_collateral,
                (1.645 * 2.0 * STDDEV(trace_disconnected_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_collateral_confidence,
                AVG(trace_connected_collateral) AS trace_connected_collateral,
                (1.645 * 2.0 * STDDEV(trace_connected_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_collateral_confidence,
                --adopting control plane
                AVG(c_plane_hijacked_adopting) AS c_plane_hijacked_adopting,
                (1.645 * 2.0 * STDDEV(c_plane_hijacked_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_adopting_confidence,
                AVG(c_plane_disconnected_adopting) AS c_plane_disconnected_adopting,
                (1.645 * 2.0 * STDDEV(c_plane_disconnected_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_adopting_confidence,
                AVG(c_plane_connected_adopting) AS c_plane_connected_adopting,
                (1.645 * 2.0 * STDDEV(c_plane_connected_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_adopting_confidence,
                --collateral control plane
                AVG(c_plane_hijacked_collateral) AS c_plane_hijacked_collateral,
                (1.645 * 2.0 * STDDEV(c_plane_hijacked_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_collateral_confidence,
                AVG(c_plane_disconnected_collateral) AS c_plane_disconnected_collateral,
                (1.645 * 2.0 * STDDEV(c_plane_disconnected_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_collateral_confidence,
                AVG(c_plane_connected_collateral) AS c_plane_connected_collateral,
                (1.645 * 2.0 * STDDEV(c_plane_connected_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_collateral_confidence,
                --adopting hidden hijacks
                AVG(visible_hijacks_adopting) AS visible_hijacks_adopting,
                (1.645 * 2.0 * STDDEV(visible_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_adopting_confidence,
                AVG(hidden_hijacks_adopting) AS hidden_hijacks_adopting,
                (1.645 * 2.0 * STDDEV(hidden_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_adopting_confidence,
                --collateral hidden hijacks
                AVG(visible_hijacks_collateral) AS visible_hijacks_collateral,
                (1.645 * 2.0 * STDDEV(visible_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_collateral_confidence,
                AVG(hidden_hijacks_collateral) AS hidden_hijacks_collateral,
                (1.645 * 2.0 * STDDEV(hidden_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_collateral_confidence
            FROM {Simulation_Results_Agg_Table.name}
        GROUP BY
            attack_type,
            subtable_name,
            adopt_pol,
            percent
        );"""
        self.execute(sql) 
