#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Graph_Data"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Reynaldo"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from pprint import pprint
from statistics import mean
from copy import deepcopy
from .enums import Policies, Non_BGP_Policies, AS_Type, Planes, Conditions
from ..utils import error_catcher, utils
from .rovpp_data_plane_statistics import ROVPP_Data_Plane_Statistics
from .rovpp_control_plane_statistics import ROVPP_Control_Plane_Statistics

class Graph_Data:
    """This class graphs the data recieved from the rovpp simulation.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'stats']

#    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)

########################
### Helper Functions ###
########################

#    @error_catcher()
    def graph_data(self, stats):
        """Formats stats for graph production"""

        self._graph(self._format_stats(stats))

    def _format_stats(self, stats):
        """Formats stats for graph creation"""

        tstats = deepcopy(stats)
        stats = tstats
        pprint(stats)
        print("shut the front door")
        for non_bgp_policy in stats:
            if non_bgp_policy == 'bgp':
                continue ########WHY IS THIS? ERROR!!!
            for percent in stats[non_bgp_policy]:
                sim = stats[non_bgp_policy][percent]
                percent_hijacked_list = []
                hijacked_for_sim = []
                not_hijacked_for_sim = []
                temp_sim = dict()
                for policy in sim:                   
                    policy_stats = sim[policy][Planes.DATA_PLANE.value]
                    hijacked_for_sim.append(
                        policy_stats[Conditions.HIJACKED.value])
                    not_hijacked_for_sim.append(
                        policy_stats[Conditions.NOT_HIJACKED.value])
                    policy_percent_hijacked = []
                    policy_info = zip(policy_stats[Conditions.HIJACKED.value],
                                      policy_stats[
                                          Conditions.NOT_HIJACKED.value])
                    include_policy=True
                    for hijacked, not_hijacked in policy_info:
                        total = hijacked + not_hijacked
                        if total == 0:
#                            include_policy=False
                            policy_percent_hijacked.append(0)
                        else:
                            policy_percent_hijacked.append(hijacked * 100 / total)
                    if include_policy:
                        temp_sim["percent_hijacked_{}".format(policy)] = mean(policy_percent_hijacked)
                # https://stackoverflow.com/a/28822227
                # Adds all policies together into a list of trials
                hijacked_for_sim_totals = list(map(sum, zip(*hijacked_for_sim)))
                not_hijacked_for_sim_totals = list(map(sum, zip(*not_hijacked_for_sim)))
                for hijacked, not_hijacked in zip(hijacked_for_sim_totals,
                                                  not_hijacked_for_sim_totals):
                    total = hijacked + not_hijacked
                    percent_hijacked_list.append(hijacked * 100 / total)
                sim["percent_hijacked_overall"] = mean(percent_hijacked_list)
                sim.update(temp_sim)
        for non_bgp_policy in stats:
            if non_bgp_policy == 'bgp':
                continue
            print("Policy: {}".format(non_bgp_policy))
            for percent in sorted(stats[non_bgp_policy]):
                print("\tpercent adoption: {}".format(percent))
                for percent_hijacked in sorted(stats[non_bgp_policy][percent]):
                    if "percent" in percent_hijacked:
                        print("\t\t{}: {}\n".format(percent_hijacked, stats[non_bgp_policy][percent][percent_hijacked]))

    def _graph(self, formatted_stats):
        pass
