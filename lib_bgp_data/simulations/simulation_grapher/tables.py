#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains Tables for graphing"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from ..simulator.tables import Simulation_Results_Table
from ...utils.database import Generic_Table

test_info = ["adopt_pol",
             "attack_type",
             "number_of_attackers",
             "subtable_name",
             "percent",
             "round_num",
             "extra_bash_arg_1",
             "extra_bash_arg_2",
             "extra_bash_arg_3",
             "extra_bash_arg_4",
             "extra_bash_arg_5"]

class Simulation_Results_Agg_Table(Generic_Table):
    """Table used to aggregate the results for graphing"""

    name = "simulation_results_agg"

    def fill_table(self):
        global test_info
        sql = f"""
        CREATE UNLOGGED TABLE {self.name} AS (
            SELECT

                {", ".join(test_info)},

                --adopting traceback
                trace_hijacked_adopting::decimal / trace_total_adopting::decimal AS trace_hijacked_adopting,
                (trace_blackholed_adopting::decimal + no_rib_adopting::decimal)::decimal / trace_total_adopting::decimal AS trace_disconnected_adopting,
                trace_nothijacked_adopting::decimal / trace_total_adopting::decimal AS trace_connected_adopting,
        
                --collateral traceback
                trace_hijacked_collateral::decimal / trace_total_collateral::decimal AS trace_hijacked_collateral,
                (trace_blackholed_collateral::decimal + no_rib_collateral::decimal)::decimal / trace_total_collateral::decimal AS trace_disconnected_collateral,
                trace_nothijacked_collateral::decimal / trace_total_collateral::decimal AS trace_connected_collateral,

                --all traceback
                (trace_hijacked_adopting::decimal + trace_hijacked_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS trace_hijacked_all,
                (trace_blackholed_adopting::decimal + no_rib_adopting::decimal + trace_blackholed_collateral::decimal + no_rib_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS trace_disconnected_all,
                (trace_nothijacked_adopting::decimal + trace_nothijacked_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS trace_connected_all,
        
                --adopting control plane
                c_plane_has_attacker_prefix_origin_adopting::decimal / trace_total_adopting::decimal AS c_plane_hijacked_adopting,
                (c_plane_has_bhole_adopting::decimal + no_rib_adopting::decimal)::decimal / trace_total_adopting::decimal AS c_plane_disconnected_adopting,
                c_plane_has_only_victim_prefix_origin_adopting::decimal / trace_total_adopting::decimal AS c_plane_connected_adopting,
        
                --collateral control plane
                c_plane_has_attacker_prefix_origin_collateral::decimal / trace_total_collateral::decimal AS c_plane_hijacked_collateral,
                (c_plane_has_bhole_collateral::decimal + no_rib_collateral::decimal)::decimal / trace_total_collateral::decimal AS c_plane_disconnected_collateral,
                c_plane_has_only_victim_prefix_origin_collateral::decimal / trace_total_collateral::decimal AS c_plane_connected_collateral,

                --all control plane
                (c_plane_has_attacker_prefix_origin_adopting::decimal + c_plane_has_attacker_prefix_origin_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS c_plane_hijacked_all,
                (c_plane_has_bhole_adopting::decimal + no_rib_adopting::decimal + c_plane_has_bhole_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS c_plane_disconnected_all,
                (c_plane_has_only_victim_prefix_origin_adopting::decimal + c_plane_has_only_victim_prefix_origin_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS c_plane_connected_all,
        
                --adopting hidden hijacks
                visible_hijacks_adopting::decimal / trace_total_adopting::decimal AS visible_hijacks_adopting,
                (trace_hijacked_adopting::decimal - visible_hijacks_adopting::decimal)::decimal / trace_total_adopting::decimal AS hidden_hijacks_adopting,
        
                --collateral hidden hijacks
                visible_hijacks_collateral::decimal / trace_total_collateral::decimal AS visible_hijacks_collateral,
                (trace_hijacked_collateral::decimal - visible_hijacks_collateral::decimal)::decimal / trace_total_collateral::decimal AS hidden_hijacks_collateral,

                --all hidden hijacks
                (visible_hijacks_adopting::decimal + visible_hijacks_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS visible_hijacks_all,
                (trace_hijacked_adopting::decimal - visible_hijacks_adopting::decimal + trace_hijacked_collateral::decimal - visible_hijacks_collateral::decimal)::decimal / (trace_total_adopting::decimal + trace_total_collateral::decimal)::decimal AS hidden_hijacks_all
        
            FROM {Simulation_Results_Table.name}
            WHERE trace_total_adopting > 0 AND trace_total_collateral > 0
        );"""
        self.execute(sql) 

class Simulation_Results_Avg_Table(Generic_Table):
    """Table used to get the confidence intervals for graphing"""

    name = "simulation_results_avg"

    def fill_table(self):
        global test_info
        sql = f"""
        CREATE UNLOGGED TABLE {self.name} AS (
            SELECT
                {", ".join(test_info)},
        
                --adopting traceback
                AVG(trace_hijacked_adopting) AS trace_hijacked_adopting,
                (1.96 * STDDEV(trace_hijacked_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_adopting_confidence,
                AVG(trace_disconnected_adopting) AS trace_disconnected_adopting,
                (1.96 * STDDEV(trace_disconnected_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_adopting_confidence,
                AVG(trace_connected_adopting) AS trace_connected_adopting,
                (1.96 * STDDEV(trace_connected_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_adopting_confidence,
                --collateral traceback
                AVG(trace_hijacked_collateral) AS trace_hijacked_collateral,
                (1.96 * STDDEV(trace_hijacked_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_collateral_confidence,
                AVG(trace_disconnected_collateral) AS trace_disconnected_collateral,
                (1.96 * STDDEV(trace_disconnected_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_collateral_confidence,
                AVG(trace_connected_collateral) AS trace_connected_collateral,
                (1.96 * STDDEV(trace_connected_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_collateral_confidence,
                --all traceback
                AVG(trace_hijacked_all) AS trace_hijacked_all,
                (1.96 * STDDEV(trace_hijacked_all))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_all_confidence,
                AVG(trace_disconnected_all) AS trace_disconnected_all,
                (1.96 * STDDEV(trace_disconnected_all))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_all_confidence,
                AVG(trace_connected_all) AS trace_connected_all,
                (1.96 * STDDEV(trace_connected_all))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_all_confidence,
                --adopting control plane
                AVG(c_plane_hijacked_adopting) AS c_plane_hijacked_adopting,
                (1.96 * STDDEV(c_plane_hijacked_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_adopting_confidence,
                AVG(c_plane_disconnected_adopting) AS c_plane_disconnected_adopting,
                (1.96 * STDDEV(c_plane_disconnected_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_adopting_confidence,
                AVG(c_plane_connected_adopting) AS c_plane_connected_adopting,
                (1.96 * STDDEV(c_plane_connected_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_adopting_confidence,
                --collateral control plane
                AVG(c_plane_hijacked_collateral) AS c_plane_hijacked_collateral,
                (1.96 * STDDEV(c_plane_hijacked_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_collateral_confidence,
                AVG(c_plane_disconnected_collateral) AS c_plane_disconnected_collateral,
                (1.96 * STDDEV(c_plane_disconnected_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_collateral_confidence,
                AVG(c_plane_connected_collateral) AS c_plane_connected_collateral,
                (1.96 * STDDEV(c_plane_connected_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_collateral_confidence,
                --all control plane
                AVG(c_plane_hijacked_all) AS c_plane_hijacked_all,
                (1.96 * STDDEV(c_plane_hijacked_all))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_all_confidence,
                AVG(c_plane_disconnected_all) AS c_plane_disconnected_all,
                (1.96 * STDDEV(c_plane_disconnected_all))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_all_confidence,
                AVG(c_plane_connected_all) AS c_plane_connected_all,
                (1.96 * STDDEV(c_plane_connected_all))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_all_confidence,
                --adopting hidden hijacks
                AVG(visible_hijacks_adopting) AS visible_hijacks_adopting,
                (1.96 * STDDEV(visible_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_adopting_confidence,
                AVG(hidden_hijacks_adopting) AS hidden_hijacks_adopting,
                (1.96 * STDDEV(hidden_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_adopting_confidence,
                --collateral hidden hijacks
                AVG(visible_hijacks_collateral) AS visible_hijacks_collateral,
                (1.96 * STDDEV(visible_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_collateral_confidence,
                AVG(hidden_hijacks_collateral) AS hidden_hijacks_collateral,
                (1.96 * STDDEV(hidden_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_collateral_confidence,
                --all hidden hijacks
                AVG(visible_hijacks_all) AS visible_hijacks_all,
                (1.96 * STDDEV(visible_hijacks_all))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_all_confidence,
                AVG(hidden_hijacks_all) AS hidden_hijacks_all,
                (1.96 * STDDEV(hidden_hijacks_all))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_all_confidence
            FROM {Simulation_Results_Agg_Table.name}
        GROUP BY
            {", ".join(test_info)}
        );"""
        self.execute(sql) 
