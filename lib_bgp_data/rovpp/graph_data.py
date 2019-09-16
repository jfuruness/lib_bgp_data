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
from .enums import Policies, Non_BGP_Policies, Planes, Conditions
from ..utils import error_catcher, utils
from .rovpp_data_plane_statistics import ROVPP_Data_Plane_Stats
from .rovpp_control_plane_statistics import ROVPP_Control_Plane_Stats

class Graph_Data:
    """This class graphs the data recieved from the rovpp simulation.

    In depth explanation at the top of the file
    """

    def __init__(self, args):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args, paths=False)

########################
### Helper Functions ###
########################

    def graph_data(self, stats, tables):
        """Formats stats for graph production"""

        self._graph(self._format_stats(stats, tables))

    def _format_stats(self, stats, tables):

        #stats = deepcopy(tstats)
        for t_obj in stats:
            for adopt_pol in stats[t_obj]:
                for i in stats[t_obj][adopt_pol]:
                    
                    for pol in stats[t_obj][adopt_pol][i]:
                        sim = stats[t_obj][adopt_pol][i][pol]
                        total_list = self.calculate_total_num_ases(sim)
                        if sum(total_list) > 0:
                            for plane in sim:
                                sim[plane]["percents"] = {
                                    cond: self.calc_avg(cond, data, total_list)
                                    for cond, data in sim[plane].items()}
        return stats
    
    def calc_avg(self, condition, data, totals):
        """Returns a dict with cond name followed by avg"""

        # Gets rid of trails where noone recieves the hijack
        data_w_totals = [(x, y) for x, y in zip(data, totals) if y != 0]
        return sum(x / y for x, y in data_w_totals) / len(data_w_totals) * 100

    def calculate_total_num_ases(self, sim):
        
        # Could this be a list comp? Sure. Are you CrAZy????
        total_list = []
        plane = Planes.CONTROL_PLANE.value
        cond = Conditions.BHOLED.value
        for trial in range(len(sim[plane][cond])):
            total_list.append(sum([sim[plane][x.value][trial]
                              for x in Conditions.__members__.values()]))
        return total_list

    def _graph(self, fstats):
        data = ""
        for t_obj in fstats:
            data += t_obj.table.name + ":\n"
            for adopt_pol in fstats[t_obj]:
                data += "\tFor adoption policy: {}:\n".format(adopt_pol)
                for i in fstats[t_obj][adopt_pol]:
                    data += "\t\tFor {}\n".format(t_obj.percents[i])
                    for pol in fstats[t_obj][adopt_pol][i]:
                        sim = fstats[t_obj][adopt_pol][i][pol]
                        total_list = self.calculate_total_num_ases(sim)
                        if total_list[0] != 0:
                            data += "\t\t\tFor {} Policy:\n".format(pol)
                            for plane in sim:
                                data += "\t\t\t\tFor {} Plane\n".format(plane)
                                for cond in sim[plane]["percents"]:
                                    data += "\t\t\t\t\t{}: {}\n".format(
                                        cond, sim[plane]["percents"][cond])

        self.logger.warning(data)
