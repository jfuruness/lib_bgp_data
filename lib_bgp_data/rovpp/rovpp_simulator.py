#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
import json
from tqdm import tqdm
from .enums import Policies, Non_BGP_Policies, Hijack_Types, Conditions
from .enums import Control_Plane_Conditions as C_Plane_Conds
from .tables import Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table
from .tables import ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table, ROVPP_All_Trials_Table
from .tables import ROVPP_Statistics_Table
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
        with db_connection(ROVPP_All_Trials_Table, self.logger) as db:
            db.clear_table()
        with db_connection(ROVPP_Statistics_Table, self.logger) as db:
            db.clear_table

        data_points = [Data_Point(trials, p_i, percent, percents, self.logger)
                       for p_i, percent in enumerate(percents)]

        # NOTE: Make this into a separate function!
        total = 0
        for data_point in data_points:
            for trial in range(data_point.total_trials):
               for test in data_point.get_possible_tests():
                    total += 1

        with tqdm(total=total, desc="Running simulator") as pbar:
            for data_point in data_points:
                data_point.get_data(self.args, pbar)
        print("Due to fixes in exr, statistics will be done later.")
        print("For now look in rovpp_all_trials table")

        return
        # NOTE: TAKE OUT JSON!!! push it all to the database.
        # Graph code should not be included.

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
        self.tables = Subtables(self.default_percents, self.logger)
        self.logger.debug("Initialized Data Point")

    def get_data(self, exr_args, pbar):
        self.run_tests(exr_args, pbar)
        self.calculate_statistics()

    def run_tests(self, exr_args, pbar):
        for trial in range(self.total_trials):
            for test in self.get_possible_tests(set_up=True):
                test.run(trial, exr_args, pbar)

    def calculate_statistics(self):
        return
        for table in self.tables:
            for test in self.get_possible_tests():
                # Calculate statistics for that data point
                # For that hijack type and adopt pol
                # NOTE: Later move this function into the table,
                # and have it callable by cond rather than a sql dict
                sql = """SELECT * FROM rovpp_all_trials
                      WHERE subtable_name = %s AND
                            hijack_type = %s AND
                            adopt_pol = %s"""
                data = [table.name, test.hijack_type, test.adopt_pol_name]

                # Store in db
                with db_connection(ROVPP_Statistics_Table, self.logger) as db:
                    trials = db.execute(sql, data)
                    
                    # FROM HERE calc avg percent using both totals
                    # STORE ALL THIS DATA INTO WHERE IT IS NEEDED TO BE GRAPHED!

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
        self.adopt_pol_name = {v.value: k for k, v in
                               Policies.__members__.items()}[self.adopt_pol]
        self.logger.debug("Initialized test")

    def __repr__(self):
        return (self.hijack, self.hijack_type, self.adopt_pol)

    def run(self, trial_num, exr_args, pbar):
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
                                         [x.table.name for x in self.tables])
        self.tables.store_trial_data(self.hijack,
                                     self.hijack_type,
                                     self.adopt_pol_name,
                                     trial_num)

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

    def store_trial_data(self, hijack, hijack_type, adopt_pol_name, trial_num):
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
                                   adopt_pol_name,
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

    def store_trial_data(self, all_ases, hijack, h_type, adopt_pol_name, tnum):


        sql = """SELECT asn, opt_flag, received_from_asn FROM
              {}""".format(self.exr_table_name)
        subtable_ases = {x["asn"]: x for x in self.table.execute(sql)}

        conds = {x.value: 0 for x in Conditions.__members__.values()}

        opt_flag_data = self._get_opt_flag_data(deepcopy(conds))
        traceback_data = self._get_traceback_data(deepcopy(conds),
                                                  subtable_ases,
                                                  all_ases)
        # Control plane received any kind of prefix that is the same as
        # the attackers, and vice versa
        control_plane_data = self._get_control_plane_data(hijack)

        with db_connection(ROVPP_All_Trials_Table) as db:
            db.insert(self.table.name,
                      hijack,
                      h_type,
                      adopt_pol_name,
                      tnum,
                      opt_flag_data,
                      traceback_data,
                      control_plane_data)

    def _get_opt_flag_data(self, conds):
        for cond in [x.value for x in Conditions.__members__.values()]:
            sql = """SELECT COUNT(*) FROM {}
                  WHERE opt_flag = {}""".format(self.exr_table_name, cond)
            conds[cond] = self.table.execute(sql)[0]["count"]
        return conds

    def _get_traceback_data(self, conds, subtable_ases, all_ases):

        possible_conditions = set(conds.keys())
        for asn, as_data in subtable_ases.items():
            while as_data["received_from_asn"] not in possible_conditions:
                asn = as_data["received_from_asn"]
                as_data = all_ases[asn]
            conds[as_data["received_from_asn"]] += 1

        return conds

    def _get_control_plane_data(self, hijack):
        c_plane_data = {}
        sql = "SELECT COUNT(*) FROM " + self.exr_table_name
        sql += " WHERE prefix = %s;"
        c_plane_data[C_Plane_Conds.RECEIVED_ATTACKER_PREFIX.value] =\
            self.table.execute(sql, [hijack.attacker_prefix])[0]["count"]
        c_plane_data[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX.value] =\
            self.table.execute(sql, [hijack.victim_prefix])[0]["count"]

        no_rib_sql = """SELECT COUNT(*) FROM {0}
                     LEFT JOIN {1} ON {0}.asn = {1}.asn WHERE {1}.asn IS NULL;
                     """.format(self.table.name, self.exr_table_name)
        c_plane_data[C_Plane_Conds.NO_RIB.value] =\
            self.table.execute(no_rib_sql)[0]["count"]

        return c_plane_data
