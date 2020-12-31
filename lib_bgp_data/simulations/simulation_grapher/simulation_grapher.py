#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Does graphing"""


__authors__ = ["Justin Furuness", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from concurrent.futures import ProcessPoolExecutor
import os

import tarfile
from tqdm import tqdm

from .enums import Graph_Formats, Policy_Combos
from .graph import Graph
from .graph_generator import Graph_Generator
from .line_formatter import Line_Formatter

from ..enums import Policies

from ...utils.base_classes import Parser
from ...utils import utils


class Simulation_Grapher(Parser):
    """Graphs output of the simulation"""

    graph_path = "/tmp/graphs"

    def _run(self,
             percents_to_graph=None,
             policy_combos=Policy_Combos.__members__.values(),
             titles=False,
             fmts=Graph_Formats.__members__.values()):

        # Deletes and creates graph path
        utils.clean_paths(self.graph_path)
        # Extracts data and gets graphs ready to plot
        graphs = Graph_Generator(**self.kwargs)._run(percents_to_graph)

        total = len(policy_combos) * len(graphs) * len(Graph_Formats)

        # Gets args for Graph.write_graph, formats for multiprocessing
        mp_args = self.get_mp_args(policy_combos, graphs, total, titles, fmts)

        with ProcessPoolExecutor() as executor:
            # https://stackoverflow.com/a/52242947/8903959
            # Tested w/both accepted and alternate answer. They are the same
            kwargs = {"total": len(mp_args[0]), "desc": "Writing graphs"}
            list(tqdm(executor.map(Graph.write_graph, *mp_args), **kwargs))
        self.tar_graphs()

    def get_mp_args(self, policy_combos_to_graph, graphs, total, titles, fmts):
        mp_graphs = []
        mp_policies = []
        mp_line_formatters = []
        mp_paths = []
        mp_fmts = []
        mp_totals = []
        mp_titles = []
        for policies in policy_combos_to_graph:
            line_formatter = Line_Formatter(policies.value)
            for graph in graphs:
                for fmt in fmts:
                    mp_graphs.append(graph)
                    mp_policies.append(policies.value)
                    mp_line_formatters.append(line_formatter)
                    mp_paths.append(self.get_save_path(policies.name, graph, fmt))
                    mp_fmts.append(fmt)
                    mp_totals.append(total)
                    mp_titles.append(titles)
        return [mp_graphs,
                mp_policies,
                mp_line_formatters,
                mp_paths,
                mp_fmts,
                mp_totals,
                mp_titles]
 
    def get_save_path(self, graph_name, graph, fmt):
        _dir = os.path.join(self.graph_path,
                            fmt.value.replace(".", ""),
                            graph.attack_type,
                            graph.subtable,
                            graph.graph_type)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        return os.path.join(_dir, graph_name + fmt.value)

    def tar_graphs(self):
        with tarfile.open(self.graph_path + ".tar.gz", "w:gz") as tar:
            tar.add(self.graph_path, arcname=os.path.basename(self.graph_path))
