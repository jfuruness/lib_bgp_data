#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
import json
from .enums import Policies, Non_BGP_Policies, Hijack_Types
from .tables import ROVPP_ASes_Table, Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table
from .rovpp_statistics import ROVPP_Statistics_Calculator as Stats_Calculator
from .rovpp_simulator_set_up import ROVPP_Simulator_Set_Up_Tool
from .graph_data import Graph_Data
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
        if not self.args.get("stream_level"):
            self.args["stream_level"] = 20 # Can't import logging, threadsafe


    @utils.run_parser(paths=False)
    def simulate(self, percents=range(5, 31, 5), trials=100, real_data=False):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Sets up all trials and percents
        Relationships_Parser(self.args).parse_files(rovpp=True)

        data_points = [Data_Point(total_trials, p_i, percent, percents)
                       for p_i, percent in enumerate(percents)]

        for data_points in data_points:
            data_point.get_data()

        print(self.toJSON())
        
        # Close all tables here!!!
        # Graph data here!!!
        # Possibly move back to iterator (below)

    # https://stackoverflow.com/a/15538391
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class Data_Point:
    def __init__(self, total_trials, percent_iter, percent, default_percents):
        self.total_trials = total_trials
        self.percent_iter = percent_iter
        self.percent = percent
        self.default_percents = default_percents
        self.stats = dict()

    def get_data(self):
        self.run_tests()
        self.calculate_statistics()

    def run_tests(self):
        for trial in range(self.total_trials):
            self.set_up_trial()
            for test in get_possible_tests(set_up_hijacks=True):
                test.run(trial)

    def calculate_statistics(self):
        for test in get_possible_tests():
            test.calculate_statistics()

    def get_possible_tests(self, set_up_hijacks=False):
        for hijack_type in [x.value for x in Hijack_Types.values]:
            if set_up_hijacks:
                hijack = self.set_up_hijack_data()
            else:
                 hijack = None
            for adopt_pol in [x.value for x in Non_BGP_Policies.values]:
                yield Test(self.tables, hijack=hijack,
                           hijack_type=hijack_type, adopt_pol=adopt_pol)

    def set_up_trial(self):
        self.tables = Subtables(default_percents)
        self.tables.set_implimentable_ases()
            
    def set_up_hijack_data(self):
        # sets hijack data
        # Also return hijack variable
        with db_connection(Subprefix_Hijack_Temp_Table, self.logger) as db:
            return db.populate(self._get_possible_hijacker_ases(), hijack_type)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)


class Test:
    def __init__(self, tables, **params):
        self.tables = tables
        self.hijack = self.params.get("hijack")
        self.hijack_type = self.params.get("hijack_type")
        self.adopt_pol = self.params.get("adopt_pol")

    def __repr__(self):
        return (self.hijack, self.hijack_type, self.adopt_pol)

    def run_sim(self, trial_num):
        # Runs sim, gets data
        self.logger.info("Trial {} with test info: {}".format(trial_num, self.params))

        self.tables.change_routing_policy(self.adopt_pol)
        Extrapolator(self.args).run_rovpp(self.hijack,
                                          [x.table.name for x in tables])
        self.tables.get_data(self.hijack, self.adopt_pol)

    def calculate_statistics(self):
        # Get data from the extrapolator output for the test
        self.get_data()
        # Should be a dict of htype: t_obj: adopting_policy: dplane: (conds with list of data) cplane: (conds with data)
        # Should save this to self.data
        for data_field in self.data_fields():
            # Average the list and calculate statistics
            # Must compare all raw data to the ROV variant
            # Save all of this to the data thing

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)

class Subtables:
    def __init__(self, default_percents):
        # Add docs on how to add a table to these sims
        # Create these tables and then 
        # Create an everything else table
        self.tables = [Subtable(ROVPP_Top_100_ASes_Table,
                                self.logger,
                                [25]*len(default_percents),
                                possible_hijacker=False),
                       Subtable(ROVPP_Edge_ASes_Table,
                                self.logger,
                                default_percents)]
        for sub_table in self.tables:
            sub_table.table.fill_table()

        etc = Subtable(ROVPP_Etc_ASes_Table, self.logger, default_percents)
        etc.table.fill_table([x.table.name for x in self.tables])
        self.tables.append(etc)

    def set_implimentable_ases(self, percent_iteration_num, attacker):

        for sub_table in self.tables:
            sub_table.set_implimentable_ases(percent_iteration_num, attacker)

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
    """Subtable class for ease of use"""

    def __init__(self,
                 table,
                 logger,
                 percents,
                 possible_hijacker=True,
                 policy_to_impliment=None):
        self.logger = logger
        self.table = table(logger)
        self.count = self.table.get_count()
        self.percents = percents
        self.possible_hijacker = possible_hijacker
        # None for whatever policy is being tested
        self.policy_to_impliment = policy_to_impliment

    def set_implimentable_ases(self, iteration_num, attacker):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)
