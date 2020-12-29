#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from tqdm import tqdm

from .graph import Graph
from .tables import Simulation_Results_Agg_Table
from .tables import Simulation_Results_Avg_Table

from ..simulator.tables import Simulation_Results_Table

from ...utils.base_classes import Parser


class Graph_Generator(Parser):
    """Generates all policy lines for graphing

    For an in depth explanation, see README
    """

    def _run(self, percents_to_graph=None):

        # Gets data to graph
        self.generate_agg_tables()
        return self.get_graph_data(percents_to_graph)

    def generate_agg_tables(self):
        for Table in [Simulation_Results_Agg_Table,
                      Simulation_Results_Avg_Table]:
            with Table(clear=True) as db:
                db.fill_table()

    def get_graph_data(self, percents_to_graph):
        """Generates all the possible lines on all graphs and fills data"""

        # Gets all possible policies, percents, subtables attacks
        # Gets this information from the database
        all_graph_attrs = self.get_graph_attrs(percents_to_graph)
        # Gets all the graphs that need to be written
        graphs = self.get_graphs(*all_graph_attrs)
        # pulls data out from the db for these graphs
        for graph in tqdm(graphs, total=len(graphs), desc="Getting data"):
            graph.get_data()
        return graphs

    def get_possible_graph_attrs(self, percents_to_graph):
        """Returns all possible graph variations that we can graph

        all possible policies, subtables, attack types, percents
        """

        percents = self.get_percents(percents_to_graph)

        with Simulation_Results_Table() as db:
            def get_data(self, attr):
                sql = f"SELECT DISTINCT {attr} FROM {db.name}"
                return [x[attr] for x in db.execute(sql)]
            attrs = ["adopt_pol", "subtable_name", "attack_type"]
            return [get_data[x] for x in attrs] + [percents]

    def get_percents(self, percents_to_graph):
        """Validate percents vs percent iters

        We used to have functionality to have different subtables adopt
        at different percentages. We removed this to make graphing easier

        Also returns the percents that are graphable
        """

        with Simulation_Results_Table() as db:
            sql = f"SELECT DISTINCT percent, percent_iter FROM {db.name}"
            percents = [x["percent"] for x in db.execute(sql)]
            err_msg = ("We removed functionality to graph different percents"
                       " at different levels due to the deadline")
            assert len(set(percents)) == len(percents), err_msg

        # Get only the percents specified (default get all)
        if percents_to_graph is not None:
            percents = [x for x in percents if x in percents_to_graph]

        return percents

    def get_graphs(self, policies, subtables, attack_types, percents):
        """Returns every possible graph

        Returns every possible graph
        (consisting of subtable, attack type, and type of graph)
        types of graphs ex: control plane hijacked, etc.
        """

        graphs = []

        for subtable in subtables:
            for attack_type in attack_types:
                for graph_type in Graph.get_possible_graph_types():
                    graphs.append(Graph(graph_type,
                                        subtable,
                                        attack_type,
                                        policies,
                                        percents))
        return graphs
