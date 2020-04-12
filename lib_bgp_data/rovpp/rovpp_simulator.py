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
        tables.fill_tables()

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
            test.run(self.subtables, exr_bash, exr_kwargs, self.percent, pbars)

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
    def __init__(self, scenario, attack, adopt_policy, subtables):
        self.scenario = scenario
        self.attack = attack
        self.adopt_policy = adopt_policy

    def run(self, subtables, exr_bash, exr_kwargs, percent, pbars):
        """Simulates a test:

        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.scenario, self.adopt_policy, percent, self.attack)
        # Changes routing policies for all subtables
        subtables.change_routing_policies(self.adopt_policy)
        # Runs the rov++ extrapolator
        ROVPP_Extrapolator_Parser(**exr_kwargs).run(tables.names, exr_bash)
        # Stores the run's data
        subtables.store(self.attack, self.scenario, self.adopt_policy, percent)


class Subtables:

    def __init__(self, percents, connect=True):

        # Note that if you want to change adoption percentage:
        # Simply change percents to a list of your choosing here

        # Add any extra tables to this initial list
        self.tables = [Subtable(Top_100_ASes_Table,
                                percents,
                                possible_attacker=False),
                       Subtable(Edge_ASes_Table, percents)]
        # Etc table must go at the end. It is all leftover ases
        self.tables.append(Subtable(Etc_ASes_Table,
                                    percents,
                                    possible_attacker=False))

        if connect:
            for table in self.tables:
                table.connect()

    def close(self):
        for table in self.tables:
            table.close()

class Subtable:
    """Subtable that we divide results into"""

    def __init__(self, Table_Class, percents, possible_attacker=True):
        self.Table = Table_Class
        self.possible_attacker = possible_attacker
        self.percents = percents

    def connect(self):
        """Connects table to database"""

        self.Table = self.Table()

    def close(self):
        """Closes connection"""

        self.Table.close()
 
class Input_Subtables(Subtables):
    """Contains subtable functionality for pre exr functions"""

    def __init__(self, percents):
        super(Input_Subtables, self).__init__(percents)
        self.input_tables = [Input_Table(x) for x in self.tables]

    def fill_input_tables(self):
        for subtable in self.input_tables:
            subtable.fill_input_table(self.tables)

    def set_adopting_ases(self, percent_iter, attacker, seeded):
        for subtable in self.input_tables:
            subtable.set_adopting_ases(percent_iter, attacker, seeded)

    def change_routing_policies(self, policy):
        """Changes the routing policy for that percentage of ASes"""

        self.logger.debug("About to change the routing policies")
        for sub_table in self.tables:
            sub_table.change_routing_policies(policy)

    @property
    def possible_hijacker_ases(self):
        possible_hijacker_ases = []
        # For all tables where possible attacker is true
        for _table in self.input_tables:
            possible_hijacker_ases.extend(_table.get_possible_attackers())
        return possible_hijacker_ases


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

class Input_Subtable(Subtable):
    """Subtable class for ease of use"""

    def set_adopting_ases(self, iteration_num, attacker, deterministic):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker, deterministic)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)

    def get_possible_attackers(self):
        possible_attackers = []
        if self.possible_attacker:
            possible_attackers = [x["asn"] for x in self.input_table.get_all()]
        return possible_attackers


class Output_Subtable(Subtable)
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
