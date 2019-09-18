#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Graph_Data"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Reynaldo"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import json
from pprint import pprint
from statistics import mean
from copy import deepcopy
from .enums import Policies, Non_BGP_Policies, Planes, Conditions, Top_Node_Policies, Hijack_Types
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
        for htype in stats:
            for top_node_pol in stats[htype]:
                for t_obj in stats[htype][top_node_pol]:
                    for adopt_pol in stats[htype][top_node_pol][t_obj]:
                        for i in stats[htype][top_node_pol][t_obj][adopt_pol]:
                            
                            for pol in stats[htype][top_node_pol][t_obj][adopt_pol][i]:
                                sim = stats[htype][top_node_pol][t_obj][adopt_pol][i][pol]
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
        pol_dict = {v.value: k for k, v in Policies.__members__.items()}
        conds_dict = {v.value: k for k, v in Conditions.__members__.items()}
        top_nodes_pol_dict = {v.value: k for k, v in Top_Node_Policies.__members__.items()}
        planes_dict = {v.value: k for k, v in Planes.__members__.items()}
        htype_dict = {v.value: k for k, v in Hijack_Types.__members__.items()}

        json_dict = dict()

        data = ""
        for htype in fstats:
            data += "For {}\n".format(htype_dict[htype])
            json_dict[htype_dict[htype]] = dict()
            for top_nodes_pol in fstats[htype]:
                data += "\t25/100 top nodes impliment: " + top_nodes_pol_dict[top_nodes_pol] + ":\n"
                json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]] = dict()
                for t_obj in fstats[htype][top_nodes_pol]:
                    data += "\t\t" + "For group of ases:" + t_obj.table.name + ":\n"
                    json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]][t_obj.table.name] = dict()
                    for adopt_pol in fstats[htype][top_nodes_pol][t_obj]:
                        data += "\t\t\tFor adoption policy: {}:\n".format(pol_dict[adopt_pol])
                        json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]][t_obj.table.name][pol_dict[adopt_pol]] = dict()

                        for i in fstats[htype][top_nodes_pol][t_obj][adopt_pol]:
                            data += "\t\t\t\tFor {}".format(t_obj.percents[i]) + "% adoption\n"
                            json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]][t_obj.table.name][pol_dict[adopt_pol]][t_obj.percents[i]] = dict()
                            for pol in fstats[htype][top_nodes_pol][t_obj][adopt_pol][i]:
                                sim = fstats[htype][top_nodes_pol][t_obj][adopt_pol][i][pol]
                                total_list = self.calculate_total_num_ases(sim)
                                if total_list[0] != 0:
                                    data += "\t\t\t\t\tFor {} Policy:\n".format(pol_dict[pol])
                                    json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]][t_obj.table.name][pol_dict[adopt_pol]][t_obj.percents[i]][pol_dict[pol]] = dict()
                                    for plane in sim:
                                        data += "\t\t\t\t\t\tFor {}\n".format(planes_dict[plane])
                                        json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]][t_obj.table.name][pol_dict[adopt_pol]][t_obj.percents[i]][pol_dict[pol]][planes_dict[plane]] = dict()
                                        for cond in sim[plane]["percents"]:
                                            data += "\t\t\t\t\t\t\t{}: {}".format(
                                                conds_dict[cond], sim[plane]["percents"][cond])
                                            json_dict[htype_dict[htype]][top_nodes_pol_dict[top_nodes_pol]][t_obj.table.name][pol_dict[adopt_pol]][t_obj.percents[i]][pol_dict[pol]][planes_dict[plane]][conds_dict[cond]] = sim[plane]["percents"][cond]
                                            data += "%\n"
    
        self.logger.warning(data)
        print(json.dumps(json_dict, indent=4, sort_keys=True))
