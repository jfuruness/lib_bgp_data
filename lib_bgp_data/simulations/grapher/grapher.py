#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Does graphing"""

from copy import deepcopy
from enum import Enum
from itertools import chain, combinations
import logging
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

from .tables import Simulation_Results_Agg_Table
from .tables import Simulation_Results_Avg_Table

from ..enums import AS_Types, Policies
from ..simulator.tables import Simulation_Results_Table

from ...utils.base_classes import Parser
from ...utils.database import Database
from ...utils import utils

__authors__ = ["Justin Furuness", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Simulation_Grapher(Parser):
    """Graphs output of the simulation"""

    graph_path = "/tmp/graphs"

    def _run(self,
             percents_to_graph=None,
             policy_combos_to_graph=[list(Policies.__members__.values())],
             titles=True):

        # Deletes and creates graph path
        utils.clean_paths(self.graph_path)
        # Extracts data and gets graphs ready to plot
        graphs = Graph_Generator._run(percents_to_graph)


        for policies in policy_combos_to_graph:
            line_formatter = Line_Formatter(pol_combo)
            for graph in graphs:
                for fmt in Graph_Formats.__members__.values():
                    graph.write_graph(policies,
                                      line_formatter,
                                      self.get_save_path(policies, graph, fmt),
                                      fmt,
                                      title=titles)
        self.tar_graphs()

    def get_save_path(self, policies, graph, fmt):
        _dir = os.path.join(self.graph_path,
                            graph.attack_type,
                            graph.subtable,
                            self.graph_type)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        title = "_".join(x.policy for x in self.lines) + fmt.value
        return os.path.join(_dir, title)

    def tar_graphs(self):
        with tarfile.open(self.graph_path + ".tar.gz", "w:gz") as tar:
            tar.add(self.graph_path, arcname=os.path.basename(self.graph_path))
