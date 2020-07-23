#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains classes for tables output by extrapolator
See README for in depth explanation
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import sys

from .enums import AS_Types
from .enums import Control_Plane_Conditions as C_Plane_Conds
from .enums import Data_Plane_Conditions 
from .tables import Simulation_Results_Table
from ..extrapolator_parser.tables import ROVPP_Extrapolator_Rib_Out_Table

class Output_Subtables:
    """Subtables that deal with the output functions from the extrapolator"""

    def store(self, attack, scenario, adopt_policy, percent, percent_iter):
        """Stores data"""

        # Gets all the asn data
        with ROVPP_Extrapolator_Rib_Out_Table() as _db:
            ases = {x["asn"]: x for x in _db.get_all()}
        # Stores the data for the specific subtables
        for table in self.tables:
            table.Rib_Out_Table.clear_table()
            table.Rib_Out_Table.fill_rib_out_table()
            table.store_output(ases,
                               attack,
                               scenario,
                               adopt_policy,
                               percent,
                               percent_iter,
                               [x.Rib_Out_Table.name for x in self.tables])


class Output_Subtable:
    """Specific subtable that deals with extrapolator output"""

    def store_output(self,
                     all_ases,
                     attack,
                     scenario,
                     adopt_policy,
                     percent,
                     percent_iter,
                     table_names):
        """Stores output in the simulation results table"""

        # All ases for that subtable
        subtable_ases = {x["asn"]: x for x in self.Rib_Out_Table.get_all()}
        # We don't want to track the attacker, faster than filtering dict comp
        for uncountable_asn in [attack.attacker_asn, attack.victim_asn]:
            if uncountable_asn in subtable_ases:
                del subtable_ases[uncountable_asn]

        # Insert the trial data into the simulation results table
        with Simulation_Results_Table() as db:
            db.insert(self.table.name,
                      attack,
                      scenario,
                      adopt_policy,
                      percent,
                      percent_iter,
                      self._get_traceback_data(subtable_ases, all_ases),
                      self._get_control_plane_data(attack),
                      self._get_visible_hijack_data(table_names))

    def _get_traceback_data(self, subtable_ases, all_ases):
        """Gets the data plane data through tracing back"""

        1/0
        # NOTE: this can easily be changed to SQL. See super optimized folder.
        conds = {x: {y: 0 for y in AS_Types.list_values()}
                 for x in Data_Plane_Conditions.list_values()}

        # For all the ases in the subtable
        for og_asn, og_as_data in subtable_ases.items():
            asn, as_data = og_asn, og_as_data
            looping = True
            # SHOULD NEVER BE LONGER THAN 64
            # Done to catch extrapolator loops
            for i in range(64):
                if (condition := as_data["received_from_asn"]) in conds:
                    conds[condition][og_as_data["impliment"]] += 1
                    looping = False
                    break
                else:
                    asn = as_data["received_from_asn"]
                    as_data = all_ases[asn]
            # NEEDED FOR EXR DEVS
            if looping:
                self._print_loop_debug_data(all_ases, og_asn, og_as_data)
        return conds

    def _get_visible_hijack_data(self, t_names):
        """Gets visible hijacks using sql for speed"""

        # NOTE: this will automatically remove attackersand victims
        # Since they will have nothing in their rib
        conds = {}
        # all_ases = " UNION ALL ".join(f"SELECT * FROM {x}" for x in t_names)

        for adopt_val in AS_Types.__members__.values():
            sql = f"""SELECT COUNT(*) FROM
                    {self.Rib_Out_Table.name} og
                    INNER JOIN {ROVPP_Extrapolator_Rib_Out_Table.name} all_ases
                        ON og.received_from_asn = all_ases.asn
                    INNER JOIN attackers
                        ON attackers.prefix = all_ases.prefix
                            AND attackers.origin = all_ases.origin
                    WHERE og.as_type = {adopt_val.value}"""
            conds[adopt_val] = self.Rib_Out_Table.get_count(sql)
        return conds

    def _print_loop_debug_data(self, all_ases, og_asn, og_as_data):
        """Prints debug information for whenever the exr breaks"""

        loop_str_list = []
        loop_asns_set = set()
        asn, as_data = og_asn, og_as_data
        for i in range(64):
            asn_str = f"ASN:{asn:<8}: {as_data}"
            loop_str_list.append(asn_str)
            asn = as_data["received_from_asn"]
            as_data = all_ases[asn]
            if asn in loop_asns_set:
                logging.error("Loop:\n\t" + "\n\t".join(loop_str_list))
                sys.exit(1)
            else:
                loop_asns_set.add(asn)

    def _get_control_plane_data(self, attack):
        """Gets control plane data using sql for speed"""

        conds = {x: {y: 0 for y in AS_Types.list_values()}
                 for x in C_Plane_Conds.list_values()}

        for adopt_val in AS_Types.list_values():
            sql = (f"SELECT COUNT(*) FROM {self.Rib_Out_Table.name}"
                   " WHERE prefix = %s AND origin = %s "
                   f" AND impliment = {bool(adopt_val)}")
            conds[C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value][adopt_val] =\
                self.Rib_Out_Table.get_count(sql, [attack.attacker_prefix,
                                                   attack.attacker_asn])
            conds[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value][adopt_val] =\
                self.Rib_Out_Table.get_count(sql, [attack.victim_prefix,
                                                   attack.victim_asn])
            conds[C_Plane_Conds.RECEIVED_BHOLE.value][adopt_val] =\
                self.Rib_Out_Table.get_count(sql, 
                    [attack.attacker_prefix,
                     Data_Plane_Conditions.BHOLED.value])

            no_rib_sql = """SELECT COUNT(*) FROM {0}
                         LEFT JOIN {1} ON {0}.asn = {1}.asn
                         WHERE {1}.asn IS NULL AND {0}.impliment = {2}
                         """.format(self.Input_Table.name,
                                    self.Rib_Out_Table.name,
                                    bool(adopt_val))
            conds[C_Plane_Conds.NO_RIB.value][adopt_val] =\
                self.Rib_Out_Table.get_count(no_rib_sql)

        return conds
