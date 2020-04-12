#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from pathos.multiprocessing import ProcessingPool
from multiprocessing import cpu_count
import sys
from math import sqrt
import matplotlib
# https://raspberrypi.stackexchange.com/a/72562
matplotlib.use('Agg')
from matplotlib.transforms import Bbox
from pathos.threading import ThreadPool
import matplotlib.pyplot as plt
from statistics import mean, variance, StatisticsError
from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
import json
import os
from tqdm import tqdm
from .enums import Non_BGP_Policies, Policies, Non_BGP_Policies, Hijack_Types, Conditions
from .enums import AS_Types, Control_Plane_Conditions as C_Plane_Conds
from .tables import Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table
from .tables import ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table, ROVPP_All_Trials_Table
from ..relationships_parser import Relationships_Parser
from ..relationships_parser.tables import AS_Connectivity_Table
from ..bgpstream_website_parser import BGPStream_Website_Parser

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROVPP_Simulator(Parser):
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """


    def _run(self,
             percents=list(range(5, 31, 5)),
             num_trials=100,
             exr_bash=None,
             seeded=False,
             seeded_trial=None):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Gets relationships table
        Relationships_Parser(**self.kwargs).parse_files()

        # Clear the table that stores all trial info
        with ROVPP_All_Trials_Table(clear=True) as _:
            pass

        tables = Subtables(percents, seeded)

        data_pts = [Data_Point(tables, i, p) for i, p in enumerate(percents)]

        assert deterministic_trial <= num_trials, "Bruh you can't do that"

        # We do this so that we can immediatly skip to the deterministic trial
        trials = [seeded_trial] if seeded_trial else list(range(num_trials))

        # The reason we run tqdm off the number of trials
        # And not number of data points is so that someone can input the
        # deterministic trial number and have it jump straight to that trial
        # In addition - the reason we have multiple bars is so that we can
        # display useful stats using the bar

        with Multiline_TQDM(len(trials)) as pbars:
            for trial in trials:
                if seeded:
                    random.seed(trial)
                for data_pt in data_pts:
                    data_pt.get_data(seeded, exr_bash, self.kwargs, pbars)
                pbars.update()

        tables.close()



class Data_Point:
    def __init__(self, subtables, percent_iter, percent):
        self.subtables = subtables
        self.percent_iter = percent_iter
        self.percent = percent

    def get_data(self, seeded, exr_bash, exr_kwargs, pbars):
        for test in self.get_possible_tests(seeded=seeded):
            test.run(exr_bash, exr_kwargs, self.percent, pbars)

    def get_possible_tests(self, set_up=True):
        for scenario in Scenarios.__members__.values():
            # Sets adopting ases, returns hijack
            attack = self.set_up_test(scenario) if set_up else None
            
            for adopt_pol in Non_Default_Policies.__members__.values():
                yield Test(scenario, attack, adopt_pol)

    def set_up_test(self, scenario):
        # Fills the hijack table
        with Hijack_Table(clear=True) as db:
            hijack = db.fill_table(self.tables.possible_hijackers, scenario)
        # Sets the adopting ases
        self.tables.set_adopting_ases(self.percent_iter, hijack.attacker_asn)
        # Return the hijack class
        return hijack

class Test:
    def __init__(self, scenario, attack, adopt_policy):
        self.scenario = scenario
        self.attack = attack
        self.adopt_policy = adopt_policy

    def run(self, exr_bash, exr_kwargs, percent, pbars):
        """Simulates a test:

        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.scenario, self.adopt_policy, percent, self.attack)
        # Changes routing policies for all subtables
        tables.change_routing_policies(self.adopt_policy)
        # Runs the rov++ extrapolator
        ROVPP_Extrapolator_Parser(**exr_kwargs).run(tables.names, exr_bash)
        # Stores the run's data
        tables.store(self.attack, self.scenario, self.adopt_policy, percent)

        
class Subtables:
    def __init__(self, default_percents, logger, _open=True):

        self.logger = logger

        # Add docs on how to add a table to these sims
        # Create these tables and then 
        # Create an everything else table
        self.tables = [Subtable(ROVPP_Top_100_ASes_Table,
                                self.logger,
                                default_percents,
                                possible_hijacker=False, _open=_open),
                       Subtable(ROVPP_Edge_ASes_Table,
                                self.logger,
                                default_percents, _open=_open)]
        if _open:
            for sub_table in self.tables:
                sub_table.table.fill_table()

        etc = Subtable(ROVPP_Etc_ASes_Table,
                       self.logger,
                       default_percents,
                       possible_hijacker=False, _open=_open)
        if _open:
            etc.table.fill_table([x.table.name for x in self.tables])
        self.tables.append(etc)
        self.logger.debug("Initialized subtables")

        self._cur_table = -1

    @staticmethod
    def create_ribs_out_tables():
        pass

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

    def close(self):
        # Should really be in the subtable class not here (but for loop should be here)
        for table in self.tables:
            table.close()


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
                 policy_to_impliment=None,
                 _open=True):
        self.logger = logger
        if _open is True:
            print("OOO")
        self.table = table(logger, _open=_open)
        self.exr_table_name = "rovpp_exr_{}".format(self.table.name)
        if _open:
            self.count = self.table.get_count()
        self.percents = percents
        self.possible_hijacker = possible_hijacker
        # None for whatever policy is being tested
        self.policy_to_impliment = policy_to_impliment

    def close(self):
        self.table.close()

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
