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
                --adopting hidden hijacks
                AVG(visible_hijacks_adopting) AS visible_hijacks_adopting,
                (1.96 * STDDEV(visible_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_adopting_confidence,
                AVG(hidden_hijacks_adopting) AS hidden_hijacks_adopting,
                (1.96 * STDDEV(hidden_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_adopting_confidence,
                --collateral hidden hijacks
                AVG(visible_hijacks_collateral) AS visible_hijacks_collateral,
                (1.96 * STDDEV(visible_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_collateral_confidence,
                AVG(hidden_hijacks_collateral) AS hidden_hijacks_collateral,
                (1.96 * STDDEV(hidden_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_collateral_confidence
            FROM {Simulation_Results_Agg_Table.name}
        GROUP BY
            attack_type,
            subtable_name,
            adopt_pol,
            percent
        );"""
        self.execute(sql) 
