#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains simulations results table

This stores all data for every trial
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from ..enums import AS_Types
from ..enums import Control_Plane_Conditions as CP_Conds
from ..enums import Data_Plane_Conditions as DP_Conds
from ..enums import Non_Default_Policies

from ...utils.database import Generic_Table


class Simulation_Results_Table(Generic_Table):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

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
                 attacker_prefixes CIDR[],
                 victim bigint,
                 victim_prefixes CIDR[],
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
                 attacker_prefixes,
                 victim,
                 victim_prefixes,
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

        test_info = [hijack.__class__.__name__,
                     subtable_name,
                     hijack.attacker,
                     "{" + ",".join(hijack.attacker_prefixes) + "}",
                     hijack.victim,
                     "{" + ",".join(hijack.victim_prefixes) + "}",
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
            cp_non_adopting[CP_Conds.RECV_ATK_PREF_ORIGIN.value],
            cp_non_adopting[CP_Conds.RECV_ONLY_VIC_PREF_ORIGIN.value],
            cp_non_adopting[CP_Conds.RECV_BHOLE.value],
            cp_non_adopting[CP_Conds.NO_RIB.value],

            cp_adopting[CP_Conds.RECV_ATK_PREF_ORIGIN.value],
            cp_adopting[CP_Conds.RECV_ONLY_VIC_PREF_ORIGIN.value],
            cp_adopting[CP_Conds.RECV_BHOLE.value],
            cp_adopting[CP_Conds.NO_RIB.value]]

        v_hjack_info = [visible_hijack_data[x] for x in 
                        [AS_Types.ADOPTING, AS_Types.COLLATERAL]]

        self.execute(sql, test_info + trace_info + cplane_info + v_hjack_info)
