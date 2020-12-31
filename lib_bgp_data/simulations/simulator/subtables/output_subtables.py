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

import logging
import sys

from ..tables import Simulation_Results_Table
from ...enums import AS_Types
from ...enums import Control_Plane_Conditions as C_Plane_Conds
from ...enums import Data_Plane_Conditions
from ....extrapolator import Simulation_Extrapolator_Forwarding_Table


class Output_Subtables:
    """Subtables that deal with the output functions from the extrapolator"""

    def store(self, attack, number_of_attackers, adopt_policy, percent, percent_iter, extra_bash):
        """Stores data"""

        # Gets all the asn data
        with Simulation_Extrapolator_Forwarding_Table() as _db:
            ases = {x["asn"]: x for x in _db.get_all()}

        # Stores the data for the specific subtables
        for table in self.tables:
            table.Forwarding_Table.clear_table()
            table.Forwarding_Table.fill_forwarding_table()
            table.store_output(ases,
                               attack,
                               number_of_attackers,
                               adopt_policy,
                               percent,
                               percent_iter,
                               extra_bash,
                               [x.Forwarding_Table.name for x in self.tables])


class Output_Subtable:
    """Specific subtable that deals with extrapolator output"""

    def store_output(self,
                     all_ases,
                     attack,
                     number_of_attackers,
                     adopt_policy,
                     percent,
                     percent_iter,
                     extra_bash_str,
                     table_names):
        """Stores output in the simulation results table"""

        # All ases for that subtable
        subtable_ases = {x["asn"]: x for x in self.Forwarding_Table.get_all()}
        # We don't want to track the attacker, faster than filtering dict comp
        for uncountable_asn in [attack.attacker, attack.victim]:
            if uncountable_asn in subtable_ases:
                del subtable_ases[uncountable_asn]

        # Insert the trial data into the simulation results table
        with Simulation_Results_Table() as db:
            db.insert(self.table.name,
                      attack,
                      number_of_attackers,
                      adopt_policy,
                      percent,
                      percent_iter,
                      extra_bash_str,
                      self._get_traceback_data(subtable_ases,
                                               all_ases,
                                               attack),
                      self._get_control_plane_data(attack),
                      self._get_visible_hijack_data(table_names, attack))

    def _get_traceback_data(self, subtable_ases, all_ases, attack):
        """Gets the data plane data through tracing back"""

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
                # Conds are end conditions. See README.
                if (condition := as_data["received_from_asn"]) in conds:
                    conds[condition][og_as_data["impliment"]] += 1
                    looping = False
                    break
                else:
                    asn = as_data["received_from_asn"]
                    as_data = all_ases[asn]

            # NEEDED FOR EXR DEVS
            # If it ends the for loop and didn't change looping...
            if looping:
                loop_data = [all_ases, og_asn, og_as_data, attack]
                self._print_loop_debug_data(*loop_data)
        return conds

    def _get_visible_hijack_data(self, t_names, attack):
        """Gets visible hijacks using sql for speed"""

        # NOTE: this will automatically remove attackers and victims
        # Since they will have nothing in their rib
        conds = {}

        # Gets one before the final AS. If that AS had the attacker,
        # Then that is a visible hijacking
        # We must include prefix and origin here due to preventive ann
        # And other blackhole mechanisms
        attacker_ann = []
        # NOTE: This won't work for path manipulation attacks
        # I set an assert statement in attack class for this
        for prefix in attack.attacker_prefixes:
            sql = "(all_ases.prefix = '{}' AND all_ases.origin = {})".format(
                prefix, attack.attacker)
            attacker_ann.append(sql)

        attacker_sql = " OR ".join(attacker_ann)

        for adopt_val in AS_Types.__members__.values():
            sql = f"""SELECT COUNT(*) FROM
                    {self.Forwarding_Table.name} og
                    INNER JOIN {Simulation_Extrapolator_Forwarding_Table.name}
                        all_ases
                            ON og.received_from_asn = all_ases.asn
                    WHERE og.as_type = {adopt_val.value} AND ({attacker_sql})
                    """
            conds[adopt_val] = self.Forwarding_Table.get_count(sql)
        return conds

    def _print_loop_debug_data(self, all_ases, og_asn, og_as_data, attack):
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
                err_str = "\n" * 20 + "Loop:\n\t"
                err_str += "\n\t".join(loop_str_list) + str(attack) + "\n" * 20
                logging.error(err_str)
                sys.exit(1)
            else:
                loop_asns_set.add(asn)

    def _get_control_plane_data(self, attack):
        """Gets control plane data using sql for speed"""

        conds = {x: {y: 0 for y in AS_Types.list_values()}
                 for x in C_Plane_Conds.list_values()}

        for adopt_val in AS_Types.list_values():
            # NOTE: we no longer do it by prefix because now an atk can
            # have multiple prefixes. Only by origin should be fine tho
            # NOTE: This will break for attack manipulation attacks
            sql = (f"SELECT COUNT(*) FROM {self.Forwarding_Table.name}"
                   " WHERE origin = %s AND asn != %s"
                   f" AND asn != %s AND impliment = {bool(adopt_val)}")
            conds[C_Plane_Conds.RECV_ATK_PREF_ORIGIN.value][adopt_val] =\
                self.Forwarding_Table.get_count(sql, [attack.attacker,
                                                      attack.attacker,
                                                      attack.victim])
            conds[C_Plane_Conds.RECV_ONLY_VIC_PREF_ORIGIN.value][adopt_val] =\
                self.Forwarding_Table.get_count(sql, [attack.victim,
                                                      attack.attacker,
                                                      attack.victim])
            conds[C_Plane_Conds.RECV_BHOLE.value][adopt_val] =\
                self.Forwarding_Table.get_count(sql,
                                         [Data_Plane_Conditions.BHOLED.value,
                                          attack.attacker,
                                          attack.victim])

            no_rib_sql = """SELECT COUNT(*) FROM {0}
                         LEFT JOIN {1} ON {0}.asn = {1}.asn
                         WHERE {1}.asn IS NULL AND {0}.impliment = {2}
                         AND {0}.asn != {3} AND {0}.asn != {4}
                         """.format(self.Input_Table.name,
                                    self.Forwarding_Table.name,
                                    bool(adopt_val),
                                    attack.attacker,
                                    attack.victim)
            # I had defaulted these to 0, but I don't think that should happen
            # So lets error if it does
            assert attack.attacker is not None
            assert attack.victim is not None

            conds[C_Plane_Conds.NO_RIB.value][adopt_val] =\
                self.Forwarding_Table.get_count(no_rib_sql)

        return conds
