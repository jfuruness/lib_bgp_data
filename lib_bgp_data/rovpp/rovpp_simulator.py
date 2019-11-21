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
from .tables import Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table, ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table
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
        # Can't import logging, threadsafe, 20=INFO
        self.args["stream_level"] = self.args.get("stream_level", 20)

    @utils.run_parser(paths=False)
    def simulate(self, percents=range(5, 31, 5), trials=100):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Sets up all trials and percents
        Relationships_Parser(self.args).parse_files(rovpp=True)
        with db_connection(ROVPP_All_trials_Table, self.logger) as db:
            db.clear_table()


        data_points = [Data_Point(trials, p_i, percent, percents, self.logger)
                       for p_i, percent in enumerate(percents)]

        for data_point in data_points:
            data_point.get_data(self.args)

        print(self.toJSON())
        
        # Close all tables here!!!
        # Graph data here!!!
        # Possibly move back to iterator (below)

    # https://stackoverflow.com/a/15538391
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class Data_Point:
    def __init__(self, total_trials, percent_iter, percent,
                 default_percents, logger):
        self.total_trials = total_trials
        self.percent_iter = percent_iter
        self.percent = percent
        self.default_percents = default_percents
        self.logger = logger
        self.stats = dict()
        self.logger.debug("Initialized Data Point")

    def get_data(self, exr_args):
        self.run_tests(exr_args)
        self.calculate_statistics()

    def run_tests(self, exr_args):
        for trial in range(self.total_trials):
            for test in self.get_possible_tests(set_up=True):
                test.run(trial, exr_args)

    def calculate_statistics(self):
        1/0

    def get_possible_tests(self, set_up=False):
        for hijack_type in [x.value for x in Hijack_Types.__members__.values()]:
            if set_up:
                hijack = self.set_up_trial(hijack_type)
            else:
                 hijack = None
            for adopt_pol in [x.value for x in
                              Non_BGP_Policies.__members__.values()]:
                yield Test(self.logger, self.tables, hijack=hijack,
                           hijack_type=hijack_type, adopt_pol=adopt_pol)

    def set_up_trial(self, hijack_type):
        self.tables = Subtables(self.default_percents, self.logger)
        # sets hijack data
        # Also return hijack variable
        with db_connection(Subprefix_Hijack_Temp_Table, self.logger) as db:
            hijack = db.populate(self.tables.possible_hijacker_ases,
                                 hijack_type)
        self.tables.set_implimentable_ases(self.percent_iter,
                                           hijack.attacker_asn)
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
        self.logger.debug("Initialized test")

    def __repr__(self):
        return (self.hijack, self.hijack_type, self.adopt_pol)

    def run(self, trial_num, exr_args):
        # Runs sim, gets data
        self.logger.info("Trial {} with test info: {}".format(trial_num, self.params))

        self.tables.change_routing_policies(self.adopt_pol)
        Extrapolator(exr_args).run_rovpp(self.hijack,
                                         [x.table.name for x in self.tables])
        self.tables.store_trial_data(self.hijack,
                                     self.hijack_type,
                                     self.adopt_pol,
                                     trial_num)

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

        etc = Subtable(ROVPP_Etc_ASes_Table, self.logger, default_percents)
        etc.table.fill_table([x.table.name for x in self.tables])
        self.tables.append(etc)
        self.logger.debug("Initialized subtables")

        self._cur_table = -1

    def __iter__(self):
        return self

    def __next__(self):
        self._cur_table += 1
        try:
            return self.tables[self._cur_table]
        except IndexError:
            self._cur_table = -1
            raise StopIteration


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
                for result in results:
                    possible_hijacker_ases.append(result["asn"])
        return possible_hijacker_ases

    def store_trial_data(self, hijack, hijack_type, adopt_pol, trial_num):
        # NOTE: Change this later, should be exr_filtered,
        # Or at the very least pass in the args required
        sql = """SELECT asn, opt_flag, received_from_asn FROM
              rovpp_extrapolation_results_filtered;"""
        with db_connection() as db:
            ases = {x["asn"]: x for x in db.execute(sql)}
        for table in self.tables:
            table.store_trial_data(ases,
                                   hijack,
                                   hijack_type,
                                   adopt_pol,
                                   trial_num)


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

    def set_implimentable_ases(self, iteration_num, attacker):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)

    def store_trial_data(self, all_ases, hijack, hijack_type, adopt_pol, tnum):
        sql = """SELECT asn, opt_flag, received_from_asn FROM
              {}""".format(self.exr_table_name)
        subtable_ases = {x["asn"]: x for x in self.table.execute(sql)}

        conds = {x.value: 0 for x in Conditions.__members__.values()}

        # Calculate No Rib
        sql = """SELECT COUNT(*) FROM (SELECT DISTINCT asn FROM {}
              EXCEPT SELECT asn FROM rovpp_ases) a""".format(
                self.exr_table_name)
        conds[Conditions.NORIB] = self.table.execute(sql)[0]["count"]

        opt_flag_data = self._get_opt_flag_data(deepcopy(conds))
        traceback_data = self._get_traceback_data(deepcopy(conds),
                                                  subtable_ases,
                                                  all_ases)

        with db_connection(All_Trial_Data_Table) as db:
            db.insert(hijack,
                      hijack_type,
                      adopt_pol,
                      tnum,
                      opt_flag_data,
                      traceback_data)

    def _get_opt_flag_data(self, conds):
        for cond in [x.value for x in Conditions.__members__.values()
                     if x.value != Conditions.NORIB.value]:
            sql = """SELECT COUNT(*) FROM {}
                  WHERE opt_flag = {}""".format(self.exr_table_name, cond)
            conds[cond] = self.table.execute(sql)[0]["count"]
        return conds

    def _get_traceback_data(self, conds, subtable_ases, all_ases):
        possible_conditions = set(conds.keys())
        for asn, as_data in subtable_ases.items():
            while as_data["received_from_asn"] not in possible_conditions:
                asn = as_data["recieved_from_asn"]
                as_data = all_ases["asn"]
            conds[as_data["received_from_asn"]] += 1
        return conds
