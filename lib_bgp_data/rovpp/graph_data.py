#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Graph_Data"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Reynaldo"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from pprint import pprint
from statistics import mean
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

        pprint(stats)
        input("shut the front door")
        for non_bgp_policy in stats:
            if non_bgp_policy == 'bgp':
                continue ########WHY IS THIS? ERROR!!!
            for percent in stats[non_bgp_policy]:
                sim = stats[non_bgp_policy][percent]
                percent_hijacked_list = []
                hijacked_for_sim = []
                not_hijacked_for_sim = []
                for policy in sim:                   
                    policy_stats = sim[policy][Planes.DATA_PLANE.value]
                    hijacked_for_sim.append(
                        policy_stats[Conditions.HIJACKED.value])
                    not_hijacked_for_sim.append(
                        policy_stats[Conditions.NOT_HIJACKED.value])
                # https://stackoverflow.com/a/28822227
                # Adds all policies together into a list of trials
                hijacked_for_sim_totals = list(map(sum, zip(*hijacked_for_sim)))
                not_hijacked_for_sim_totals = list(map(sum, zip(*not_hijacked_for_sim)))
                for hijacked, not_hijacked in zip(hijacked_for_sim_totals,
                                                  not_hijacked_for_sim_totals):
                    total = hijacked + not_hijacked
                    percent_hijacked_list.append(hijacked * 100 / total)
                sim["percent_hijacked"] = mean(percent_hijacked_list)
        for non_bgp_policy in stats:
            if non_bgp_policy == 'bgp':
                continue
            print("Policy: {}".format(non_bgp_policy))
            for percent in stats[non_bgp_policy]:
                print("\tpercent adoption: {}".format(percent))
                print("\tpercent hijacked: {}\n".format(
                    stats[non_bgp_policy][percent]["percent_hijacked"]))

    def _graph(self, formatted_stats):
        pass
