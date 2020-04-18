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

import ipaddress
import logging
from random import sample

from tqdm import tqdm

from .attack import Attack
from .enums import Non_Default_Policies, Policies, Attack_Types
from .enums import AS_Types, Data_Plane_Conditions as DP_Conds
from .enums import Control_Plane_Conditions as CP_Conds

from ..database import Database, Generic_Table
from ..mrt_parser.tables import MRT_Announcements_Table
from ..relationships_parser.tables import AS_Connectivity_Table, ASes_Table
# Done this way to avoid circular imports

class Tests_Table(Generic_Table):
    name = "tests"

    def fill_table(self, policies, attack_types, possible_attackers):
        """Creates a table of all prefix and policy adoption pairs

        The list index goes up by 1 every time
        The policy index goes up to the max policy then back to 0
        """

        atk_dict = {k: [] for k in attack_types}

        assert len(atk_dict) <= 3, "Must mod this func for more attacks"

        for i in range(0, 254, len(atk_dict)):
            for n in range(254):
                # Cameron wrote prefix generation code
                # Should generate prefixes that do not overlap with each other

                # Subprefix attacks
                if Attack_Types.SUBPREFIX_HIJACK in attack_types:
                    sub_atk_pref = ipaddress.ip_network(((i<<24) + (n<<16), 24))
                    sub_vic_pref = ipaddress.ip_network(((i<<24) + (n<<16), 16))
                    subprefix_atk = Attack(sub_atk_pref, sub_vic_pref)
                    atk_dict[Attack_Types.SUBPREFIX_HIJACK].append(subprefix_atk)
                # Prefix attacks
                if Attack_Types.PREFIX_HIJACK in attack_types:
                    pref_atk = ipaddress.ip_network((((i+1)<<24) + (n<<16), 24))
                    pref_vic = ipaddress.ip_network((((i+1)<<24) + (n<<16), 24))
                    prefix_attack = Attack(pref_atk, pref_vic)
                    atk_dict[Attack_Types.PREFIX_HIJACK].append(prefix_attack)
                # Non compete attacks
                if Attack_Types.UNANNOUNCED_PREFIX_HIJACK in attack_types:
                    non_comp_pref = ipaddress.ip_network((((i+2)<<24) + (n<<16), 16))
                    non_comp = Attack(non_comp_pref)
                    atk_dict[Attack_Types.UNANNOUNCED_PREFIX_HIJACK].append(non_comp)

        num_attacks = len(atk_dict[Attack_Types.SUBPREFIX_HIJACK])

        # Must create attacker victim pairs here equal to number of attacks - len policies
        attacker_victim_pairs = [sample(possible_attackers, k=2)
                                 for x in range(num_attacks * len(atk_dict))]


        with tqdm(total=num_attacks * len(atk_dict), desc="Generating attacks") as pbar:

            # There is prob a way to do it in a for loop but whatever
            list_index = 0
            attack_index = 0
            while attack_index < num_attacks - len(policies):
                for attack_type in atk_dict:
                    attacker_victim_pair = attacker_victim_pairs[list_index]
                    for i, policy_value in enumerate([x.value for x in policies]):
                        attack = atk_dict[attack_type][attack_index + i]
                        attack.add_info(list_index, policy_value, attack_type, attacker_victim_pair)
                        pbar.update()
                    list_index += 1
                attack_index += len(policies)


class Simulation_Announcements_Table(Generic_Table):
    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                 prefix cidr,
                 as_path bigint ARRAY,
                 origin bigint,
                 list_index integer,
                 policy_val smallint
                 );"""
        self.execute(sql)
        

class Attackers_Table(Simulation_Announcements_Table):
    name = "attackers"

class Victims_Table(Simulation_Announcements_Table):
    name = "victims"

# Fix this later
from ..extrapolator_parser.tables import ROVPP_Extrapolator_Rib_Out_Table

#################
### Subtables ###
#################

class Subtable_Rib_Out(Generic_Table):

    def fill_rib_out_table(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
              SELECT a.asn, a.prefix, a.origin, a.received_from_asn,
                b.as_type, b.adopting
                FROM {ROVPP_Extrapolator_Rib_Out_Table.name} a
              INNER JOIN {self.input_name} b
                ON a.asn = b.asn);"""
        self.execute(sql)

class Top_100_ASes_Table(ASes_Table):
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
                 SELECT a.asn, ARRAY[]::BOOLEAN[] AS as_types
                FROM {ASes_Table.name} a WHERE asn = {ases_str}
                 );"""              
        self.cursor.execute(sql)


class Top_100_ASes_Rib_Out_Table(Top_100_ASes_Table, Subtable_Rib_Out):
    name = "top_100_ases_rib_out"


class Edge_ASes_Table(ASes_Table):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "edge_ases"

    @property
    def Rib_Out_Table(self):
        return Edge_ASes_Rib_Out_Table

    def fill_table(self, *args):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS edge_ases AS (
                     SELECT r.asn, ARRAY[]::BOOLEAN[] AS as_types
                         FROM {ASes_Table.name} r
                         INNER JOIN {AS_Connectivity_Table.name} c
                            ON c.asn = r.asn
                     WHERE c.connectivity = 0
                 );"""
        self.execute(sql)

class Edge_ASes_Rib_Out_Table(Edge_ASes_Table, Subtable_Rib_Out):
    name = "edge_ases_rib_out"


class Etc_ASes_Table(ASes_Table):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    input_name = name = "etc_ases"

    @property
    def Rib_Out_Table(self):
        return Etc_ASes_Rib_Out_Table

    def fill_table(self, table_names):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                 SELECT ra.asn, ARRAY[]::BOOLEAN[] AS as_types
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
                 attack_type,
                 subtable_name,
                 attacker_asn,
                 attacker_prefix,
                 victim,
                 victim_prefix,
                 adopt_pol,
                 percent,
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
                      %s, %s, %s, %s);"""

        # Also write out cp = control plane dp = dataplane everywhere
        # Had to do it, things where so insanely long unreadable

        # Splits dicts up for readability
        traceback_non_adopting = {k: type_dict[AS_Types.NON_ADOPTING.value]
                                  for k, type_dict in traceback_data.items()}
        traceback_adopting = {k: type_dict[AS_Types.ADOPTING.value]
                              for k, type_dict in traceback_data.items()}
        cp_non_adopting = {k: type_dict[AS_Types.NON_ADOPTING.value]
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
                     percent]

        traceback_info = [
            traceback_non_adopting[DP_Conds.HIJACKED.value],
            traceback_non_adopting[DP_Conds.NOTHIJACKED.value],
            traceback_non_adopting[DP_Conds.BHOLED.value],
            total_traceback_non_adopting,

            traceback_adopting[DP_Conds.HIJACKED.value],
            traceback_adopting[DP_Conds.NOTHIJACKED.value],
            traceback_adopting[DP_Conds.BHOLED.value],
            total_traceback_adopting]

        control_plane_info = [
            cp_non_adopting[CP_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
            cp_non_adopting[CP_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
            cp_non_adopting[CP_Conds.RECEIVED_BHOLE.value],
            cp_non_adopting[CP_Conds.NO_RIB.value],

            cp_adopting[CP_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
            cp_adopting[CP_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
            cp_adopting[CP_Conds.RECEIVED_BHOLE.value],
            cp_adopting[CP_Conds.NO_RIB.value]]

        self.execute(sql, test_info + traceback_info + control_plane_info)
