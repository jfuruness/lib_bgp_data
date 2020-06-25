#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Does graphign"""

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

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Simulation_Grapher(Parser):
    graph_path = "/tmp/graphs"

    def _run(self, percents_to_graph=None):
        if os.path.exists(self.graph_path):
            shutil.rmtree(self.graph_path)
        os.makedirs(self.graph_path)


        self.generate_agg_tables()
        scenarios_dict = self.populate_policy_lines(percents_to_graph)
        total = 0
        for tkiz in [True, False]:
            for scenario, policies_dict in scenarios_dict.items():
                for policy_list in self.powerset_of_policies(policies_dict.keys()):
                    total += 1
        
#        with tqdm(total=total, desc="graphing") as pbar:
        with utils.Pool(None, 1, "graph pool") as p:
            line_types = []
            subtables = []
            attack_types = []
            all_lines = []
            tkiz_l = []
            save_paths = []
            for tkiz in [True, False]:
                for scenario, policies_dict in scenarios_dict.items():
                    line_type, subtable, attack_type = scenario
                    for policy_list in self.powerset_of_policies(policies_dict.keys()):
                        lines = [v for k, v in policies_dict.items()
                                 if k in set(policy_list)]
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
                  [total] * total,
                  tkiz_l,
                  save_paths)
        self.tar_graphs()

    def generate_agg_tables(self):
        for Table in [Simulation_Results_Agg_Table,
                      Simulation_Results_Avg_Table]:
            with Table(clear=True) as db:
                db.fill_table()

    def populate_policy_lines(self, percents_to_graph):
        """Generates all the possible lines on all graphs and fills data"""
        pols, percents, subtables, attacks = self.get_possible_graph_attrs()
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
        """Write the graph for whatever subset of liens you have"""

        # https://stackoverflow.com/a/47930319/8903959
        file_count = sum(len(files) for _, _, files in os.walk(self.graph_path))
        # https://stackoverflow.com/a/5419488/8903959
        print(f"Writing {'tkiz' if tkiz else 'png'} {file_count}/{total}\r", end="")
        sys.stdout.flush()
        # policy name | name in graph | line style | line marker | line color
        # NOTE: there's enough of these that this should prob be a class
        labels_dict = {"ROV": ("ROV", "-", ".", "b"),
                       "ROVPP": ("ROV++v1", "--", "1", "g"),
                       "ROVPPB": ("ROV++v2a", "-.", "*", "r"),
                       "ROVPPBP": ("ROV++v3", ":", "x", "c"),
                       "ROVPPBIS": ("ROV++v2", "solid", "d", "m"),
                       "ROVPP_V0": ("ROVPP_V0", "dotted", "2", "y"),
                       "BGP": ("BGP", "dashdot", "3", "k"),
                       "ROVPP_LITE": ("ROV++v1_LIGHT", "dashed", "4", "w"),
                       # NOTE: this is messed up, fix it, matplotlib is OUT OF COLORS
                       "ROVPPB_LITE": ("ROV++v2a", "-.", "*", "b"),
                       "ROVPPBP_LITE": ("ROV++v3", ":", "x", "r"),
                       "ROVPPBIS_LITE": ("ROV++v2", "solid", "d", "y"),
                       }
        fig, ax = plt.subplots()
        for line in lines:
            label, style, marker, color = labels_dict[line.policy]
            ax.errorbar(line.data[Graph_Values.X],
                        line.data[Graph_Values.Y],
        #                yerr=line.data[Graph_Values.YERR],
                        label=label,
                        ls=style,
                        marker=marker,
                        color=color)
        ax.set_ylabel("Percent_" + line.line_type)
        ax.set_xlabel(f"Percent adoption")
        ax.set_title(f"{subtable} and {attack_type}")
        ax.legend()
        plt.tight_layout()
        policies = "_".join(x.policy for x in lines)
        if tkiz:
            tikzplotlib.save(os.path.join(save_path, f"{policies}.tex"))
        else:
            plt.savefig(os.path.join(save_path, f"{policies}.png"))
        plt.close(fig)

    def tar_graphs(self):
        with tarfile.open(self.graph_path + ".tar.gz", "w:gz") as tar:
            tar.add(self.graph_path, arcname=os.path.basename(self.graph_path))

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
                self.data[Graph_Values.X].append(int(result["percent"] * 100))
                self.data[Graph_Values.Y].append(float(result[self.line_type]))
#                self.data[Graph_Values.YERR].append(float(
#                    result[self.conf_line_type]))


