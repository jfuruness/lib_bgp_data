#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Does graphing"""

from copy import deepcopy
from enum import Enum
from itertools import chain, combinations
import os
import sys

import matplotlib
# https://raspberrypi.stackexchange.com/a/72562
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tikzplotlib
import shutil
import tarfile
from tqdm import tqdm

from .enums import AS_Types
from .tables import Simulation_Results_Table
from .tables import Simulation_Results_Agg_Table
from .tables import Simulation_Results_Avg_Table

from ..base_classes import Parser
from ..database import Database
from ..utils import utils

__authors__ = ["Justin Furuness", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

matplotlib.rcParams['lines.markersize'] = 10


class Simulation_Grapher(Parser):
    """Graphs output of the simulation"""

    graph_path = "/tmp/graphs"

    def _run(self, percents_to_graph=None, test=True, tkiz=False):
        if os.path.exists(self.graph_path):
            shutil.rmtree(self.graph_path)
        os.makedirs(self.graph_path)


        self.generate_agg_tables()
        scenarios_dict = self.populate_policy_lines(percents_to_graph)
        total = 0
        graphs = list(self.graph_permutations(scenarios_dict, test, tkiz))

        with utils.Pool(None, 1, "graph pool") as p:
            line_types = []
            subtables = []
            attack_types = []
            all_lines = []
            tkiz_l = []
            save_paths = []
            for tkiz, line_type, subtable, attack_type, policy_list, policies_dict in graphs:
                lines = [v for k, v in policies_dict.items() if k in set(policy_list)]
                # They want this hardcoded in, whatever
                if (line_type == Line_Type.DATA_PLANE_HIJACKED.value.format("adopting")
                    and subtable == "edge_ases"
                    and attack_type == "subprefix_hijack"):
                        hardcoded_line = scenarios_dict[("hidden_hijacks_adopting",
                                                        "edge_ases",
                                                     "subprefix_hijack")]["ROV"]
                        hardcoded_line = deepcopy(hardcoded_line)
                        hardcoded_line.policy = "rov_hidden_hijack_adopting"
                        lines.append(hardcoded_line)
                line_types.append(line_type)
                subtables.append(subtable)
                attack_types.append(attack_type)
                all_lines.append(lines)
                tkiz_l.append(tkiz)
                tkiz_folder = "tkiz" if tkiz else "pngs"
                save_path = os.path.join(self.graph_path,
                                         tkiz_folder,
                                         attack_type,
                                         subtable,
                                         line_type)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                save_paths.append(save_path)
            p.map(self.write_graph,
                  line_types,
                  subtables,
                  attack_types,
                  all_lines,
                  [len(graphs)] * len(graphs),
                  tkiz_l,
                  save_paths)

        self.graph_deltas(scenarios_dict, tkiz)
        self.rov_data_v_ctrl(scenarios_dict, tkiz)
        self.tar_graphs()

    def rov_data_v_ctrl(self, scenarios_dict, tkiz):
        # Hard coded graph for ROV policy. There should be one graph for each
        # subtable and each attack has three subtables. I know this is really
        # janky but this was what was easiest for me to code

        # Get the graph attributes
        (policies, percents, subtables, attack_types) = self.get_possible_graph_attrs()

        # Empty dictionary to hold the lines for each graph
        rov_lines = {}

        # Each attack type will be a key in the rov_lines dictionary. The
        # value for each key will be another dictionary that contains the lines
        # to be graphed for each subtable
        for attack_type in attack_types:
            rov_lines[attack_type] = {subtable: [] for subtable in subtables}

        # These are the ROV policy line types we are interested in graphing
        line_types = ['c_plane_hijacked_adopting',
                      'c_plane_hijacked_collateral',
                      'trace_hijacked_adopting',
                      'trace_hijacked_collateral']

        # The scenarios dictionary should already contain the lines we want to
        # graph, we just need to get them and append the lines to their
        # appropriate list in the dictionary 
        for attack, attack_dict in rov_lines.items():
            for subtable in attack_dict.keys():
                for line_type in line_types:
                    line = scenarios_dict[(line_type, subtable, attack)]['ROV']
                    line.policy = 'rov_' + line_type
                    attack_dict[subtable].append(line)

        # Graph the lines. This code is very similar to the write_graphs
        # method. However, custom axis labels are needed and the method
        # uses predefined axis labels. Also, the write graphs function prints
        # out how many pngs have been written. Since this graph isn't in the
        # output of graph permutations, the printed updates won't be accurate.
        labels_dict = self.get_graph_labels()
        for attack, attack_dict in rov_lines.items():
            for subtable, lines in attack_dict.items():
                fig, ax = plt.subplots()
                for line in lines:
                    label = labels_dict[line.policy]
                    ax.errorbar(line.data[Graph_Values.X],
                                line.data[Graph_Values.Y],
                                yerr=line.data[Graph_Values.YERR],
                                label=label.name,
                                ls=label.style,
                                marker=label.marker,
                                color=label.color)
                ax.set_ylabel("Percent Hijacked")
                ax.set_xlabel("Percent Adoption")
                ax.legend()
                plt.tight_layout()
                plt.rcParams.update({'font.size': 14})
                save_path = os.path.join(self.graph_path,
                                         "tkiz" if tkiz else "pngs",
                                         attack,
                                         subtable,
                                         ("rov_cntrl_plane_v_data_plane_"
                                          "adopting_and_collateral"))
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                if tkiz:
                    tikzplotlib.save(os.path.join(save_path, "rov_hijacks_percent.tex"))
                else:
                    plt.savefig(os.path.join(save_path, "rov_hijacks_percent.png"))
                plt.close()

    def graph_deltas(self, scenarios_dict, tkiz):
        """This function graphs the deltas in the simulation. Purpose is to
        see how each policy compares to ROV++V1"""

        # These are the line_types we are interested in comparing
        line_types_to_graph = ['trace_hijacked_collateral',
                               'trace_hijacked_adopting',
                               'trace_connected_collateral',
                               'trace_connected_adopting',
                               'trace_disconnected_collateral',
                               'trace_disconnected_adopting']

        # Get all the different graphs that need to be graphed
        graphs = list(self.get_delta_graphs(scenarios_dict,
                                            set(line_types_to_graph),
                                            tkiz))

        # Graph each graph
        for tkiz, line_type, subtable, attack_type, policy_list, policies_dict in graphs:
            rovpp_line = policies_dict['ROVPP']
            labels_dict = self.get_graph_labels()
            fig, ax = plt.subplots()
            for policy, line in policies_dict.items():
                if policy in {'ROVPP', 'BGP', 'ROV', 'ROVPPB', 'ROVPPB_LITE', 'ROVPP_V0'}:
                    continue
                label = labels_dict[line.policy]
                ax.errorbar(line.data[Graph_Values.X],
                            [ly - ry for ry, ly in zip(rovpp_line.data[Graph_Values.Y],
                                                       line.data[Graph_Values.Y])],
                            #yerr=line.data[Graph_Values.YERR],
                            label=label.name,
                            ls=label.style,
                            marker=label.marker,
                            color=label.color)
            y_label = ""
            if  "trace_hijacked" in line_type:
                y_label = "Data Plane % Hijacked"
            elif "trace_connected" in line_type:
                y_label = "Data Plane % Successful Connection"
            elif "trace_disconnected" in line_type:
                y_label = "Data Plane % Disconnected"
            else:
                y_label = "Percent_" + line_type
            ax.set_ylabel(y_label)
            ax.set_xlabel("Percent Adoption")
            ax.legend()
            plt.tight_layout()
            plt.rcParams.update({'font.size': 14})
            save_path = os.path.join(self.graph_path,
                                     "tkiz" if tkiz else "pngs",
                                     attack_type,
                                     subtable,
                                     "rovpp_delta_" + line_type)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            if tkiz:
                tikzplotlib.save(os.path.join(save_path, "rovpp_delta_" + line_type + ".tex"))
            else:
                plt.savefig(os.path.join(save_path, "rovpp_delta_" + line_type + ".png"))
            plt.close()
            
    def get_delta_graphs(self, scenarios_dict, line_types_to_graph, tkiz):
        """Produces the graphs that need to be graphed"""

        for scenario, policies_dict in scenarios_dict.items():
            line_type, subtable, attack_type = scenario
            if line_type not in line_types_to_graph:
                continue
            policy_list = list(policies_dict.keys())
            #policy_list = ["ROVPPBIS", "ROVPPBP",
            #               "ROVPP_LITE", "ROVPPB_LITE", "ROVPPBP_LITE"],
            yield tkiz, line_type, subtable, attack_type, policy_list, policies_dict

    def graph_permutations(self, scenarios_dict, test, graph_tkiz):
        for scenario, policies_dict in scenarios_dict.items():
            line_type, subtable, attack_type = scenario
            if test:
                powerset = [list(policies_dict.keys()),
                            ["ROVPP", "ROVPPBIS", "ROVPPBP",
                             "ROVPP_LITE", "ROVPPBIS_LITE", "ROVPPBP_LITE"],
                            ["ROV", "rov_hidden_hijack_adopting",
                             "ROVPP", "ROVPPBIS", "ROVPPBP",
                             "ROVPP_LITE", "ROVPPBIS_LITE", "ROVPPBP_LITE"],
                            ["rov_hidden_hijack_adopting",
                             "ROVPP", "ROVPPBIS", "ROVPPBP",
                             "ROVPP_LITE", "ROVPPBIS_LITE", "ROVPPBP_LITE"],
                            ["BGP"]]
            else:
                powerset = self.powerset_of_policies(policies_dict.keys())
            for policy_list in powerset:
                yield graph_tkiz, line_type, subtable, attack_type, policy_list, policies_dict
 
    def generate_agg_tables(self):
        for Table in [Simulation_Results_Agg_Table,
                      Simulation_Results_Avg_Table]:
            with Table(clear=True) as db:
                db.fill_table()

    def populate_policy_lines(self, percents_to_graph):
        """Generates all the possible lines on all graphs and fills data"""
        pols, percents, subtables, attacks = self.get_possible_graph_attrs()
        for policy in pols:
            err_msg = "Must add line style for that policy in get_graph_labels"
            assert policy in self.get_graph_labels(), err_msg
        if percents_to_graph is not None:
            percents = [x for x in percents if x in percents_to_graph]
        policy_lines_dict = self.get_policy_lines(pols,
                                                  percents,
                                                  subtables,
                                                  attacks)
        total = 0
        for policy_dict in policy_lines_dict.values():
            for policy_line in policy_dict.values():
                total += 1

        with tqdm(total=total, desc="Populating line data") as pbar:
            for policy_dict in policy_lines_dict.values():
                for policy_line in policy_dict.values():
                    policy_line.populate_data()
                    pbar.update()
        return policy_lines_dict

    def get_possible_graph_attrs(self):
        """Returns all possible graph attributes"""

        with Simulation_Results_Table() as db:
            sql = f"SELECT DISTINCT adopt_pol FROM {db.name}"
            policies = [x["adopt_pol"] for x in db.execute(sql)]
            sql = f"SELECT DISTINCT percent_iter, percent FROM {db.name}"
            percents = [x["percent"] for x in db.execute(sql)]
            err_msg = ("We removed functionality to graph different percents"
                       " at different levels due to the deadline")
            assert len(set(percents)) == len(percents), err_msg
            sql = f"SELECT DISTINCT subtable_name FROM {db.name}"
            subtables = [x["subtable_name"] for x in db.execute(sql)]
            sql = f"SELECT DISTINCT attack_type FROM {db.name}"
            attack_types = [x["attack_type"] for x in db.execute(sql)]

        return policies, percents, subtables, attack_types

    def get_policy_lines(self, policies, percents, subtables, attack_types):
        """Returns every possible policy line class"""

        policy_dict = {}

        for subtable in subtables:
            for attack_type in attack_types:
                for line_type in get_possible_lines():
                    scenario = (line_type, subtable, attack_type)
                    policy_dict[scenario] = {policy: Policy_Line(*scenario,
                                                                 policy,
                                                                 percents)
                                             for policy in policies}
        return policy_dict

    # https://stackoverflow.com/a/1482316
    def powerset_of_policies(self, policies):

        return chain.from_iterable(combinations(policies, r)
                                   for r in range(1, len(policies) + 1))

    def write_graph(self,
                    line_type,
                    subtable,
                    attack_type,
                    lines,
                    total,
                    tkiz,
                    save_path):
        """Write the graph for whatever subset of lines you have"""

        # https://stackoverflow.com/a/47930319/8903959
        file_count = sum(len(files) for _, _, files in os.walk(self.graph_path))
        # https://stackoverflow.com/a/5419488/8903959
        print(f"Writing {'tkiz' if tkiz else 'png'} {file_count}/{total}\r", end="")
        sys.stdout.flush()
        labels_dict = self.get_graph_labels()
        fig, ax = plt.subplots()
        for line in lines:
            label = labels_dict[line.policy]
            ax.errorbar(line.data[Graph_Values.X],
                        line.data[Graph_Values.Y],
                        yerr=line.data[Graph_Values.YERR],
                        label=label.name,
                        ls=label.style,
                        marker=label.marker,
                        color=label.color)
        y_label = ""
        if  "trace_hijacked" in line_type:
            y_label = "Data Plane % Hijacked"
        elif "trace_connected" in line_type:
            y_label = "Data Plane % Successful Connection"
        elif "trace_disconnected" in line_type:
            y_label = "Data Plane % Disconnected"
        else:
            y_label = "Percent_" + line_type
        ax.set_ylabel(y_label)
        ax.set_xlabel(f"Percent adoption")
        #ax.set_title(f"{subtable} and {attack_type}")
        ax.legend()
        plt.tight_layout()
        plt.rcParams.update({'font.size': 15})
        policies = "_".join(x.policy for x in lines)
        if tkiz:
            tikzplotlib.save(os.path.join(save_path, f"{len(policies)}_{policies}.tex"))
        else:
            plt.savefig(os.path.join(save_path, f"{len(policies)}_{policies}.png"))
        plt.close(fig)

    def tar_graphs(self):
        with tarfile.open(self.graph_path + ".tar.gz", "w:gz") as tar:
            tar.add(self.graph_path, arcname=os.path.basename(self.graph_path))

    def get_graph_labels(self):
        return {"ROV": Label("ROV", "-", ".", "b"),
                "ROVPP": Label("ROV++v1", "--", "P", "g"),
                "ROVPPB": Label("ROV++v2a", "-.", "*", "r"),
                "ROVPPBP": Label("ROV++v3", ":", "X", "c"),
                "ROVPPBIS": Label("ROV++v2", "solid", "d", "m"),
                "ROVPP_V0": Label("ROVPP_V0", "dotted", "v", "y"),
                "BGP": Label("BGP", "dashdot", "3", "k"),
                "ROVPP_LITE": Label("ROV++v1_Lite", "dashed", "h", "g"),
                "ROVPPB_LITE": Label("ROV++v2a_Lite", "dotted", "s", "r"),
                "ROVPPBP_LITE": Label("ROV++v3_Lite", "-", "*", "c"),
                "ROVPPBIS_LITE": Label("ROV++v2_Lite", "-.", "^", "m"),
                "rov_hidden_hijack_adopting": Label("ROV_hidden_hijacks",
                                                    "dashed",
                                                    ">",
                                                    "b"),
                "rov_c_plane_hijacked_adopting": Label("ROV_Adopting_ctrl",
                                                       "dashed",
                                                       ".",
                                                       "b"),
                "rov_c_plane_hijacked_collateral": Label("ROV_Collateral_ctrl",
                                                         "dashed",
                                                         ".",
                                                         "r"),
                "rov_trace_hijacked_adopting": Label("ROV_Adopting_data",
                                                     "dashed",
                                                     ".",
                                                     "g"),
                "rov_trace_hijacked_collateral": Label("ROV_Collateral_data",
                                                       "dashed",
                                                       ".",
                                                       "y"),
                }

class Label:
    def __init__(self, name, style, marker, color):
        self.name = name
        self.style = style
        self.marker = marker
        self.color = color

class Line_Type(Enum):
    DATA_PLANE_HIJACKED = "trace_hijacked_{}"
    DATA_PLANE_DISCONNECTED = "trace_disconnected_{}"
    DATA_PLANE_SUCCESSFUL_CONNECTION = "trace_connected_{}"
    CONTROL_PLANE_HIJACKED = "c_plane_hijacked_{}"
    CONTROL_PLANE_DISCONNECTED = "c_plane_disconnected_{}"
    CONTROL_PLANE_SUCCESSFUL_CONNECTION = "c_plane_connected_{}"
    HIDDEN_HIJACK_VISIBLE_HIJACKED = "visible_hijacks_{}"
    HIDDEN_HIJACK_HIDDEN_HIJACKED = "hidden_hijacks_{}"
    HIDDEN_HIJACK_ALL_HIJACKED = "trace_hijacked_{}"

class Graph_Values(Enum):
    X = 0
    Y = 1
    YERR = 2
    STRS = 3

def get_possible_lines(confidence=False):
    for line_type in Line_Type.__members__.values():
        for as_type in AS_Types.__members__.values():
            name = AS_Types(as_type.value).name.lower()
            if confidence is False:
                yield line_type.value.format(name, "")
            else:
                yield line_type.value.format(name, "_confidence")
class Policy_Line:
    """This class represents a policy line on a graph"""

    def __init__(self, line_type, subtable, attack_type, policy, percents):
        """Saves class attributes and creates data dict"""

        self.policy = policy
        self.subtable = subtable
        self.attack_type = attack_type
        self.percents = percents
        self.data = {}
        self.line_type = line_type
        self.conf_line_type = self.line_type + "_confidence"
        self.data = {x: [] for x in Graph_Values.__members__.values()}

    def populate_data(self):
        with Database() as db:
            sql = f"""SELECT * FROM {Simulation_Results_Avg_Table.name}
                  WHERE subtable_name = '{self.subtable}'
                    AND adopt_pol = '{self.policy}'
                    AND attack_type = '{self.attack_type}'
                  ORDER BY percent"""
            results = db.execute(sql)
        for result in results:
            if result["percent"] in set(self.percents):
                self.data[Graph_Values.X].append(int(result["percent"]))
                self.data[Graph_Values.Y].append(float(result[self.line_type]) * 100)
                self.data[Graph_Values.YERR].append(float(result[self.conf_line_type]) * 100)

