#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
from .enums import Policies, Non_BGP_Policies
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


    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        self.set_up_tool = ROVPP_Simulator_Set_Up_Tool(args)
        self.args = args
        self.graph_data = Graph_Data(args)

    @error_catcher()
    @utils.run_parser()
    def simulate(self, percents=range(5, 31, 5), trials=100, real_data=False):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """


        self.set_up_tool.set_up_all_trials_and_percents()
        self.statistics_calculator = None
        # For each percent adoption
        for i, percent in enumerate(percents):
            # For each trial in that percent
            for t_num in range(trials):
                tables, sub_hijacks = self.set_up_tool.set_up_trial(percents,
                                                                    i)
                if self.statistics_calculator is None:
                    self.statistics_calculator = Stats_Calculator(percents,
                                                                  tables,
                                                                  self.args)

                
                for policy in Non_BGP_Policies.__members__.values():
                    # Run that specific simulation
                    self._run_sim(policy.value, tables, i, sub_hijacks, t_num,
                                  percent)

        self.graph_data.graph_data(self.statistics_calculator.stats, tables)
        # Close all tables here!!!

########################
### Helper Functions ###
########################

    @error_catcher()
    def _run_sim(self, policy, tables, i, subprefix_hijack, t_num, percent):
        """Runs one single simulation with the extrapolator"""

        self.logger.info("Running policy: {} default \%: {} trial: {}".format(
            policy, percent, t_num))

        self._change_routing_policy(tables, policy)

        Extrapolator().run_rovpp(subprefix_hijack["attacker"],
                                 subprefix_hijack["victim"],
                                 subprefix_hijack["more_specific_prefix"])

        self.statistics_calculator.calculate_stats(subprefix_hijack, i, policy)

    @error_catcher()
    def _change_routing_policy(self, tables, policy):
        """Changes the routing policy for that percentage of ASes"""

        # NOTE: maybe make this a new table func with a rename for better speed?
        # TEST IT OUT!!!
        # Also, test index vs no index
        self.logger.info("About to change the routing policies")
        for sub_table in tables:
            sub_table.change_routing_policies(policy)

        # TAKE OUT LATER - extrapolator should just accept multiple tables
        union_sql = """CREATE TABLE rovpp_ases AS (
                    SELECT * FROM {}""".format(tables[0].table.name)
        for t_obj in tables[1:]:
            union_sql += " UNION (SELECT * FROM {})".format(t_obj.table.name)
        union_sql += ");"
        sqls = ["DROP TABLE IF EXISTS rovpp_ases", union_sql]
        for sql in sqls:
            tables[0].table.execute(sql)
