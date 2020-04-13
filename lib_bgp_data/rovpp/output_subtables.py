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

class Output_Subtables:
    def store(self, attack, scenario, adopt_policy, percent):
        # Gets all the asn data
        with ROVPP_Extrapolator_Rib_Out_Table() as _db:
            ases = {x["asn"]: x for x in _db.get_all()}
        # Stores the data for the specific subtables
        for table in self.tables:
            table.Rib_Out_Table.rib_out_table.clear_table()
            table.Rib_Out_Table.fill_table()
            table.store_output(ases, attack, scenario, adopt_policy, percent)


class Output_Subtable:
    def store_output(self, all_ases, attack, scenario, adopt_policy, percent):

        subtable_ases = {x["asn"]: x for x in self.Rib_Out_Table.get_all()}
        # We don't want to track the attacker, faster than filtering dict comp
        if attack.attacker_asn in subtable_ases:
            del subtable_ases[attack.attacker_asn]

        with db_connection(Simulation_Results_Table) as db:
            db.insert(self.table.name,
                      attack,
                      scenario,
                      adopt_policy,
                      percent,
                      self._get_traceback_data(subtable_ases, all_ases),
                      self._get_control_plane_data(attack))

    def _get_traceback_data(self, subtable_ases, all_ases):
        conds = {x: {y: 0 for y in AS_Types.list_values()}
                 for x in Conditions.list_values()}

        # For all the ases in the subtable
        for og_asn, og_as_data in subtable_ases.items():
            asn, as_data = og_asn, og_as_data
            looping = True
            # SHOULD NEVER BE LONGER THAN 64
            for i in range(64):
                if (condition := as_data["received_from_asn"]) in conds:
                    conds[condition][og_as_data["adopting"]] += 1
                    looping = False
                    break
                else:
                    asn = as_data["received_from_asn"]
                    as_data = all_ases[asn]
            # NEEDED FOR EXR DEVS
            if looping:
                self._print_loop_debug_data(all_ases, og_asn, og_as_data)
        return conds

    def _print_loop_debug_data(self, all_ases, og_asn, og_as_data):
        loop_str_list = []
        loop_asns_set = set()
        asn, as_data = og_asn, og_as_data
        for i in range(64):
            asn_str = f"ASN:{self.asn:<8}: {self.adopting}"
            loop_str_list.append(asn_str)
            asn = as_data["received_from_asn"]
            as_data = all_ases[asn]
            if asn in loop_asns_set:
                logging.error("Loop:\n\t" + "\n\t".join(loop_str_list))
                sys.exit(1)
            else:
                loop_asns_set.add(asn)

    def _get_control_plane_data(self, attack):
        conds = {x: {y: 0 for y in AS_Types.list_values()}
                 for x in C_Plane_Conds.list_values()}

        for adopt_val in AS_Types.list_values():
            sql = (f"SELECT COUNT(*) FROM {self.output_table.output_name}"
                   " WHERE prefix = %s AND origin = %s "
                   f" AND adopting = {adopt_val}")
            conds[C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value] =\
                self.Rib_Out_Table.get_count(sql, [attack.attacker_prefix,
                                                   attack.attacker_asn])
            conds[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value] =\
                self.Rib_Out_Table.get_count(sql, [attack.victim_prefix,
                                                   attack.victim_asn])
            c_plane_data[C_Plane_Conds.RECEIVED_BHOLE.value] =\
                self.Rib_Out_Table.get_count(sql, [attack.attacker_prefix,
                                                   Conditions.BHOLED.value])

            no_rib_sql = """SELECT COUNT(*) FROM {0}
                         LEFT JOIN {1} ON {0}.asn = {1}.asn
                         WHERE {1}.asn IS NULL AND {0}.adopting = {2}
                         """.format(self.Table.name,
                                    self.Rib_Out_Table.name,
                                    adopt_val)
            c_plane_data[C_Plane_Conds.NO_RIB.value] =\
                self.Rib_Out_Table.get_count(no_rib_sql)

        return c_plane_data
