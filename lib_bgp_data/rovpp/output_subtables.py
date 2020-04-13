#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run
our sims, this module has turned into hardcoded crap. Fixing it now."""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Output_Subtables(Subtables):
    def __init__(self, percents):
        super(Output_Subtables, self).__init__(percents)
        self.output_tables = [Output_Table(x) for x in self.tables]

    def store(self, attack, scenario, adopt_policy, percent):
        # Gets all the asn data
        with ROVPP_Extrapolator_Rib_Out_Table() as _db:
            ases = {x["asn"]: x for x in _db.get_all()}
        # Stores the data for the specific subtables
        for table in self.output_tables:
            table.store(ases, attack, scenario, adopt_policy, percent)


class Output_Subtable(Subtable):
    def store(self, all_ases, attack, scenario, adopt_policy, percent):

        subtable_ases = {x["asn"]: x for x in self.output_table.execute(sql)}
        # Basically, {Condition: {Adopting: 0, Not adopting: 1}
        conds = {x.value: {y.value: 0 for y in AS_Types.__members__.values()}
                 for x in Conditions.__members__.values()}
        traceback_data = self._get_traceback_data(deepcopy(conds),
                                                  subtable_ases,
                                                  all_ases,
                                                  hijack,
                                                  h_type,
                                                  adopt_pol_name)
        # Control plane received any kind of prefix that is the same as
        # the attackers, and vice versa
        control_plane_data = {x.value: self._get_control_plane_data(hijack,
                                                                    x.value)
                              for x in AS_Types.__members__.values()}

        with db_connection(ROVPP_All_Trials_Table) as db:
            db.insert(self.table.name,
                      attack,
                      scenario,
                      adopt_policy,
                      percent,
                      traceback_data,
                      control_plane_data)

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
                self.table.get_count(sql, [attack.attacker_prefix,
                                           attack.attacker_asn])
            conds[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value] =\
                self.table.get_count(sql, [hijack.victim_prefix,
                                           hijack.victim_asn])
            c_plane_data[C_Plane_Conds.RECEIVED_BHOLE.value] =\
                self.table.get_count(sql, [hijack.attacker_prefix,
                                           Conditions.BHOLED.value])

            no_rib_sql = """SELECT COUNT(*) FROM {0}
                         LEFT JOIN {1} ON {0}.asn = {1}.asn
                         WHERE {1}.asn IS NULL AND {0}.adopting = {2}
                         """.format(self.input_table.name,
                                    self.output_table.name,
                                    adopt_val)
            c_plane_data[C_Plane_Conds.NO_RIB.value] =\
                self.table.get_count(no_rib_sql)

        return c_plane_data
