#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
from .enums import Policies, Non_BGP_Policies, Top_Node_Policies, Hijack_Types
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
            INFO = 20   # Can't import logging causes multithreading errors
            self.args["stream_level"] = INFO

        self.set_up_tool = ROVPP_Simulator_Set_Up_Tool(self.args)
        self.graph_data = Graph_Data(self.args)
        self.stats_time_arr = []

    @utils.run_parser(paths=False)
    def simulate(self, percents=range(5, 31, 5), trials=100, real_data=False):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """


        self.statistics_calculator = None

        self.set_up_tool.set_up_all_trials_and_percents()

        for hijack_type in Hijack_Types.__members__.values():
            for top_nodes_pol in Top_Node_Policies.__members__.values():
                # For each percent adoption
                for i, percent in enumerate(percents):
                    # For each trial in that percent
                    for t_num in range(trials):
                        tables, sub_hijacks = self.set_up_tool.set_up_trial(percents,
                                                                            i,
                                                                            top_nodes_pol.value,
                                                                            hijack_type.value)
                        if self.statistics_calculator is None:
                            self.statistics_calculator = Stats_Calculator(self.args,
                                                                          percents,
                                                                          tables)
               
                        for policy in Non_BGP_Policies.__members__.values():
                            # Run that specific simulation
                            self._run_sim(policy.value, tables, i, sub_hijacks, t_num,
                                          percent, top_nodes_pol.value, hijack_type.value)

        for t_obj in tables:
            t_obj.table.close()

        self.graph_data.graph_data(self.statistics_calculator.stats, tables)
        print(sum(self.stats_time_arr)/len(self.stats_time_arr))
        # Close all tables here!!!

########################
### Helper Functions ###
########################

    def _run_sim(self, policy, tables, i, subprefix_hijack, t_num, percent, top_nodes_pol, hijack_type):
        """Runs one single simulation with the extrapolator"""

        self.logger.info("Running Hijack type: {} top_node_pol: {} policy: {} default \%: {} trial: {}".format(
            hijack_type, top_nodes_pol, policy, percent, t_num))

        self._change_routing_policy(tables, policy)

        Extrapolator(self.args).run_rovpp(
                                subprefix_hijack["attacker"],
                                 subprefix_hijack["victim"],
                                 subprefix_hijack["more_specific_prefix"],
                                [x.table.name for x in tables])

        self.stats_time_arr.append(self.statistics_calculator.calculate_stats(subprefix_hijack, i, policy, top_nodes_pol, hijack_type))

    def _change_routing_policy(self, tables, policy):
        """Changes the routing policy for that percentage of ASes"""

        # NOTE: maybe make this a new table func with a rename for better speed?
        # TEST IT OUT!!!
        # Also, test index vs no index
        self.logger.debug("About to change the routing policies")
        for sub_table in tables:
            sub_table.change_routing_policies(policy)
