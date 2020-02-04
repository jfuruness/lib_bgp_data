#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

import sys
from math import sqrt
import matplotlib.pyplot as plt
from statistics import mean, variance, StatisticsError
from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
import json
import os
from tqdm import tqdm
from .enums import Policies, Non_BGP_Policies, Hijack_Types, Conditions
from .enums import AS_Types, Control_Plane_Conditions as C_Plane_Conds
from .tables import Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table
from .tables import ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table, ROVPP_All_Trials_Table
from ..relationships_parser import Relationships_Parser
from ..relationships_parser.tables import ROVPP_AS_Connectivity_Table
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..extrapolator import Extrapolator
from ..utils import utils, Database, Config, error_catcher, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROVPP_Simulator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """


    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args, paths=False)
        self.args = args
        # Can't import logging, threadsafe, 20=INFO
        self.args["stream_level"] = self.args.get("stream_level", 20)

    @utils.run_parser(paths=False)
    def simulate(self,
                 percents=range(5, 31, 5),
                 trials=100,
                 exr_bash=None,
                 exr_test=False,
                 deterministic=False,
                 deterministic_trial=None):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Sets up all trials and percents
        Relationships_Parser(self.args).parse_files(rovpp=True)
        with db_connection(ROVPP_All_Trials_Table, self.logger) as db:
            db.clear_table()

        data_points = [Data_Point(trials, p_i, percent, percents, self.logger)
                       for p_i, percent in enumerate(percents)]

        # NOTE: Make this into a separate function!
        total = 0
        for data_point in data_points:
            for trial in range(data_point.total_trials):
               for test in data_point.get_possible_tests():
                    total += 1
        # Change this later!
        if deterministic and deterministic_trial is not None:
            total = 0
            for data_point in data_points:
               for test in data_point.get_possible_tests():
                    total += 1

        with tqdm(total=total, desc="Running simulator") as pbar:
            for data_point in data_points:
                data_point.get_data(self.args,
                                    pbar,
                                    deterministic,
                                    deterministic_trial,
                                    exr_bash,
                                    exr_test)

        # Close all tables here!!!
        # Graph data here!!!
        # Possibly move back to iterator (below)

    def gen_graphs(self, trials=20, percents=range(5,31,5)):
        with tqdm(total=324, desc="Generating subplots") as pbar:
            utils.clean_paths(self.logger, ["/tmp/bgp_pics"])
            data_points = [Data_Point(trials, p_i, percent, percents, self.logger)
                           for p_i, percent in enumerate(percents)]
            for hijack_type in [x.value for x in Hijack_Types.__members__.values()]:
                self.gen_ctrl_plane_graphs(data_points, hijack_type, pbar)
                self.gen_data_plane_graphs(data_points, hijack_type, pbar)

    def gen_ctrl_plane_graphs(self, data_points, hijack_type, pbar):
            ctrl_val_strs = [["c_plane_has_attacker_prefix_origin"],
                             ["c_plane_has_only_victim_prefix_origin"],
                             ["c_plane_has_bhole", "no_rib"]]
            ctrl_titles = ["Control Plane Hijacked",
                           "Control Plane Successful Connection",
                           "Control Plane Disconnected"]
            self.gen_graph(data_points, ctrl_val_strs, hijack_type, ctrl_titles, "ctrl", pbar)

    def gen_data_plane_graphs(self, data_points, hijack_type, pbar):
            data_val_strs = [["trace_hijacked", "trace_preventivehijacked"],
                             ["trace_nothijacked", "trace_preventivenothijacked"],
                             ["trace_blackholed", "no_rib"]]
            data_titles = ["Data Plane Hijacked",
                           "Data Plane Successful Connection",
                           "Data Plane Disconnected"]
            self.gen_graph(data_points, data_val_strs, hijack_type, data_titles, "data", pbar)
            


    def gen_graph(self, data_points, val_strs_list, hijack_type, titles, g_title, pbar):
        fig, axs = plt.subplots(len(val_strs_list), len(data_points[0].tables))
        fig.set_size_inches(18.5, 10.5)
        pol_name_dict = {v.value: k for k, v in Non_BGP_Policies.__members__.items()}
        for i, table in enumerate(data_points[0].tables):
            for j, vals in enumerate(zip(val_strs_list, titles)):
                # Graphing Hijacked
                ax = axs[i,j]
                legend_vals = []
                for pol in [x.value for x in Non_BGP_Policies.__members__.values()]:
                    sql_data = [hijack_type,
                                table.table.name,
                                pol_name_dict[pol]]
                    self._gen_subplot(data_points, vals[0], sql_data, ax, hijack_type, vals[1], pol_name_dict[pol], pbar, pol)
                # Must be done here so as not to be set twice
                ax.set(xlabel="% adoption", ylabel=table.table.name)
                ax.title.set_text("{} for {}".format(vals[1], hijack_type))
                if "hijacked" in vals[1].lower():
                    loc="lower left"
                else:
                    loc = "upper left"
                ax.legend(loc=loc)
                # Force Y to go between 0 and 100
                ax.set_ylim(0, 100)
#                ax.title.set_text(table.table.name)
#                plt.ylabel("{} for {}".format(g_title, hijack_type), axes=ax)
#                plt.xlabel("% adoption", axes=ax)
        fig.tight_layout()
#        plt.show()
        fig.savefig("/tmp/bgp_pics/{}_{}".format(g_title, hijack_type))

    def _gen_subplot(self, data_points, val_strs, sql_data, ax, hijack_type, title, adopt_pol, pbar, pol):
        for as_type in ["_collateral"]:#["_adopting"]:#["_collateral", "_adopting"]:
            X = []
            Y = []
            Y_err = []
            for data_point in data_points:
                try:
                    sql = "SELECT " + ", ".join([x + as_type for x in val_strs])
                    sql += """, trace_total""" + as_type
                    sql += """ FROM rovpp_all_trials WHERE
                               hijack_type = %s AND
                               subtable_name = %s AND
                               adopt_pol = %s AND
                               percent_iter = %s"""
                    with db_connection(logger=self.logger) as db:
                        query = db.cursor.mogrify(sql, sql_data + [data_point.percent_iter]).decode('UTF-8')
                        results = db.execute(sql, sql_data + [data_point.percent_iter])
                        raw = [sum(x[y + as_type] for y in val_strs) * 100 / x["trace_total" + as_type] for x in results]

                        X.append(data_point.default_percents[data_point.percent_iter])
                        if data_point.default_percents[data_point.percent_iter] == 0:
#                            print("FUCK")
#                            print(query)
                            pass
                        Y.append(mean(raw))
                        Y_err.append(1.645 * 2 * sqrt(variance(raw))/sqrt(len(raw)))
                except ZeroDivisionError:
                    continue  # 0 nodes for that
                except StatisticsError as e:
                    self.logger.error(f"Statistics error. {e} Probably need more than one trial for the following query:")
                    self.logger.error(f"Query: {query}")
                    self.logger.error(raw)
                    self.logger.error(results)
                    sys.exit(1)
            styles = ["-", "--", "-.", ":", "solid", "dotted", "dashdot", "dashed"]
            markers = [".", "1", "*", "x", "d", "2", "3", "4"]
            assert pol < len(styles), "Must add more styles, sorry no time deadline"
            line = ax.errorbar(X, Y, yerr=Y_err, label=adopt_pol + as_type, ls=styles[pol], marker=markers[pol])
        pbar.update(1)


class Data_Point:
    def __init__(self, total_trials, percent_iter, percent,
                 default_percents, logger):
        self.total_trials = total_trials
        self.percent_iter = percent_iter
        self.percent = percent
        self.default_percents = default_percents
        self.logger = logger
        self.stats = dict()
        self.tables = Subtables(self.default_percents, self.logger)
        self.logger.debug("Initialized Data Point")

    def get_data(self, exr_args, pbar, seeded, seeded_trial, exr_bash, exr_test):
        self.run_tests(exr_args, pbar, seeded, seeded_trial, exr_bash, exr_test)

    def run_tests(self, exr_args, pbar, seeded, seeded_trial, exr_bash, exr_test):
        for trial in range(self.total_trials):
            if seeded:
                random.seed(trial)
                if seeded_trial and trial != seeded_trial:
                    continue
            for test in self.get_possible_tests(set_up=True, deterministic=seeded):
                test.run(trial, exr_args, pbar, self.percent_iter, exr_bash, exr_test)

    def get_possible_tests(self, set_up=False, deterministic=False):
        for hijack_type in [x.value for x in Hijack_Types.__members__.values()]:
            if set_up:
                hijack = self.set_up_test(hijack_type, deterministic)
            else:
                 hijack = None
            for adopt_pol in [x.value for x in
                              Non_BGP_Policies.__members__.values()]:
                yield Test(self.logger, self.tables, hijack=hijack,
                           hijack_type=hijack_type, adopt_pol=adopt_pol)

    def set_up_test(self, hijack_type, deterministic):
        self.tables = Subtables(self.default_percents, self.logger)
        # sets hijack data
        # Also return hijack variable
        with db_connection(Subprefix_Hijack_Temp_Table, self.logger) as db:
            hijack = db.populate(self.tables.possible_hijacker_ases,
                                 hijack_type)
        self.tables.set_implimentable_ases(self.percent_iter,
                                           hijack.attacker_asn,
                                           deterministic)
        return hijack
            
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)


class Test:
    def __init__(self, logger, tables, **params):
        self.logger = logger
        self.tables = tables
        self.params = params
        self.hijack = self.params.get("hijack")
        self.hijack_type = self.params.get("hijack_type")
        self.adopt_pol = self.params.get("adopt_pol")
        self.adopt_pol_name = {v.value: k for k, v in
                               Policies.__members__.items()}[self.adopt_pol]
        self.logger.debug("Initialized test")

    def __repr__(self):
        return (self.hijack, self.hijack_type, self.adopt_pol)

    def run(self, trial_num, exr_args, pbar, percent_iter, exr_bash, exr_test):
        # Runs sim, gets data
        pbar.set_description("{}, {}, atk {}, vic {} ".format(
                                    self.hijack_type,
                                    self.adopt_pol_name,
                                    self.hijack.attacker_asn,
                                    self.hijack.victim_asn))
        pbar.refresh()

        self.tables.change_routing_policies(self.adopt_pol)
        # DEBUG = 10, ERROR = 40
        exr_args["stream_level"] = 10 if self.logger.level == 10 else 40
        Extrapolator(exr_args).run_rovpp(self.hijack,
                                         [x.table.name for x in self.tables],
                                         exr_bash,
                                         exr_test,
                                         self.adopt_pol)
        self.tables.store_trial_data(self.hijack,
                                     self.hijack_type,
                                     self.adopt_pol_name,
                                     trial_num,
                                     percent_iter)

        pbar.update(1)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)

class Subtables:
    def __init__(self, default_percents, logger):

        self.logger = logger

        # Add docs on how to add a table to these sims
        # Create these tables and then 
        # Create an everything else table
        self.tables = [Subtable(ROVPP_Top_100_ASes_Table,
                                self.logger,
                                default_percents,
                                possible_hijacker=False),
                       Subtable(ROVPP_Edge_ASes_Table,
                                self.logger,
                                default_percents)]
        for sub_table in self.tables:
            sub_table.table.fill_table()

        etc = Subtable(ROVPP_Etc_ASes_Table,
                       self.logger,
                       default_percents,
                       possible_hijacker=False)
        etc.table.fill_table([x.table.name for x in self.tables])
        self.tables.append(etc)
        self.logger.debug("Initialized subtables")

        self._cur_table = -1

    def __len__(self):
        return len(self.tables)

    def __iter__(self):
        return self

    def __next__(self):
        self._cur_table += 1
        try:
            return self.tables[self._cur_table]
        except IndexError:
            self._cur_table = -1
            raise StopIteration


    def set_implimentable_ases(self, percent_iteration_num, attacker, deterministic):

        for sub_table in self.tables:
            sub_table.set_implimentable_ases(percent_iteration_num, attacker, deterministic)

    def change_routing_policies(self, policy):
        """Changes the routing policy for that percentage of ASes"""

        # NOTE: maybe make this a new table func with a rename for better speed?
        # TEST IT OUT!!!
        # Also, test index vs no index
        self.logger.debug("About to change the routing policies")
        for sub_table in self.tables:
            sub_table.change_routing_policies(policy)

    @property
    def possible_hijacker_ases(self):
        possible_hijacker_ases = []
        for _table in self.tables:
            if _table.possible_hijacker:
                results = _table.table.get_all()
                for result in results:
                    possible_hijacker_ases.append(result["asn"])
        return possible_hijacker_ases

    def store_trial_data(self, hijack, hijack_type, adopt_pol_name, trial_num, percent_iter):
        # NOTE: Change this later, should be exr_filtered,
        # Or at the very least pass in the args required
        sql = """SELECT asn, received_from_asn, alternate_as FROM
              rovpp_extrapolation_results_filtered;"""
        with db_connection(logger=self.logger) as db:
            ases = {x["asn"]: x for x in db.execute(sql)}
        for table in self.tables:
            table.store_trial_data(ases,
                                   hijack,
                                   hijack_type,
                                   adopt_pol_name,
                                   trial_num,
                                   percent_iter)

class Subtable:
    """Subtable class for ease of use"""

    def __init__(self,
                 table,
                 logger,
                 percents,
                 possible_hijacker=True,
                 policy_to_impliment=None):
        self.logger = logger
        self.table = table(logger)
        self.exr_table_name = "rovpp_exr_{}".format(self.table.name)
        self.count = self.table.get_count()
        self.percents = percents
        self.possible_hijacker = possible_hijacker
        # None for whatever policy is being tested
        self.policy_to_impliment = policy_to_impliment

    def set_implimentable_ases(self, iteration_num, attacker, deterministic):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker, deterministic)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)

    def store_trial_data(self, all_ases, hijack, h_type, adopt_pol_name, tnum, percent_iter):
        sql = """SELECT asn, received_from_asn, prefix, origin, alternate_as, impliment FROM {}""".format(self.exr_table_name)
        subtable_ases = {x["asn"]: x for x in self.table.execute(sql)}
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

#        pprint(traceback_data)
#        pprint(control_plane_data)

        with db_connection(ROVPP_All_Trials_Table) as db:
            db.insert(self.table.name,
                      hijack,
                      h_type,
                      adopt_pol_name,
                      tnum,
                      percent_iter,
                      traceback_data,
                      control_plane_data)

    def _get_traceback_data(self, conds, subtable_ases, all_ases, hijack, h_type, adopt_pol_name):
        possible_conditions = set(conds.keys())
        for og_asn, og_as_data in subtable_ases.items():
            # NEEDED FOR EXR DEVS
            looping = True
            asn = og_asn
            as_data = og_as_data
            # Could not use true here but then it becomes very long and ugh
            # SHOULD NEVER BE LONGER THAN 64
            for i in range(64):
                if as_data["received_from_asn"] in possible_conditions:
                    # Preventative announcements
#                    if as_data["alternate_as"] != 0:
#                        if as_data["received_from_asn"] == Conditions.HIJACKED.value:
#                            conds[Conditions.PREVENTATIVEHIJACKED.value][og_as_data["impliment"]] += 1
#                            self.logger.debug("Just hit preventive hijacked in traceback")
#                        else:
#                            conds[Conditions.PREVENTATIVENOTHIJACKED.value][og_as_data["impliment"]] += 1
#                            self.logger.debug("Just hit preventive not hijacked in traceback")
#                    # Non preventative announcements
                            # MUST ADD PREVENTIVE BLACKHOLES - THIS SHOULD JUST TRACE BACK TO ALL CONDITIONS!!!!
#                    else:
                        # TODO: SPELLING WRONG
                     conds[as_data["received_from_asn"]][og_as_data["impliment"]] += 1
                     looping = False
                     break
                else:
                    asn = as_data["received_from_asn"]
                    as_data = all_ases[asn]
            # NEEDED FOR EXR DEVS
            if looping:
                self._print_loop_debug_data(all_ases, og_asn, og_as_data, hijack, h_type, adopt_pol_name)
        ########## ADD STR METHOD TO HIJACK
        return conds

    def _print_loop_debug_data(self, all_ases, og_asn, og_as_data, hijack, h_type, adopt_pol_name):
        class ASN:
            def __init__(self, asn, implimenting):
                self.asn = asn
                self.implimenting = implimenting
            def __repr__(self):
                return f"ASN:{self.asn:<8}: {self.implimenting}"
        debug_loop_list = []
        debug_loop_set = {}
        asn = og_asn
        as_data = og_as_data
        for i in range(64):
            debug_loop_list.append(ASN(asn, as_data["impliment"]))
            asn = as_data["received_from_asn"]
            as_data = all_ases[asn]
            if asn in debug_loop_set:
                loop_strs = ["Loop was found with:",
                             f"Adopt policy: {adopt_pol_name}",
                             f"{hijack}",
                             f"hijack_type: {h_type}",
                             "loop path:",
                             "\t" + "\n\t".join(str(x) for x in debug_loop_list) + "\n"]

                self.logger.error("\n".join(loop_strs))
                sys.exit(1)
            else:
                debug_loop_set.add(asn)

    def _get_control_plane_data(self, hijack, impliment):
        c_plane_data = {}
        sql = "SELECT COUNT(*) FROM " + self.exr_table_name
        sql += " WHERE prefix = %s AND origin = %s AND impliment = " + ("TRUE" if impliment else "FALSE") + ";"
        c_plane_data[C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value] =\
            self.table.execute(sql, [hijack.attacker_prefix,
                                     hijack.attacker_asn])[0]["count"]
        c_plane_data[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value] =\
            self.table.execute(sql, [hijack.victim_prefix,
                                     hijack.victim_asn])[0]["count"]
        c_plane_data[C_Plane_Conds.RECEIVED_BHOLE.value] =\
            self.table.execute(sql, [hijack.attacker_prefix,
                                     Conditions.BHOLED.value])[0]["count"]


        no_rib_sql = """SELECT COUNT(*) FROM {0}
                     LEFT JOIN {1} ON {0}.asn = {1}.asn
                     WHERE {1}.asn IS NULL AND {0}.impliment =
                     """.format(self.table.name, self.exr_table_name)
        c_plane_data[C_Plane_Conds.NO_RIB.value] =\
            self.table.execute(no_rib_sql + ("TRUE" if impliment else "FALSE") + ";")[0]["count"]

        return c_plane_data
