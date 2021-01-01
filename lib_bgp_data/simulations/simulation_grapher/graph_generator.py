#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from concurrent.futures import ProcessPoolExecutor
import itertools

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

    def _run(self, x_axis_pts, x_axis_col):

        # Gets data to graph
        self.generate_agg_tables()
        return self.get_graph_data(x_axis_pts, x_axis_col)

    def generate_agg_tables(self):
        for Table in [Simulation_Results_Agg_Table,
                      Simulation_Results_Avg_Table]:
            with Table(clear=True) as db:
                db.fill_table()

    def get_graph_data(self, x_axis_pts, x_axis_col):
        """Generates all the possible lines on all graphs and fills data"""

        # Gets all possible policies, percents, subtables attacks
        # Gets this information from the database
        graph_attrs, x_axis_attrs, policies = self.get_graph_attrs(x_axis_pts,
                                                                   x_axis_col)
        # Gets all the graphs that need to be written
        graphs = self.get_graphs(graph_attrs,
                                 x_axis_attrs,
                                 x_axis_col,
                                 policies)
        counter = 0
        # pulls data out from the db for these graphs
        with ProcessPoolExecutor() as executor:
            # https://stackoverflow.com/a/52242947/8903959
            # Tested w/both accepted and alternate answer. They are the same
            kwargs = {"total": len(graphs), "desc": "Loading db data"}
            return graph_attrs, list(tqdm(executor.map(Graph.get_data, graphs),
                                          **kwargs))

    def get_graph_attrs(self, x_axis_pts, x_axis_col):
        """Returns all possible graph variations that we can graph

        all possible policies, subtables, attack types, percents
        """

        self.validate_percents()

        with Simulation_Results_Table() as db:
            def get_data(attr):
                sql = f"SELECT DISTINCT {attr} FROM {db.name}"
                return [x[attr] for x in db.execute(sql)]
            attrs = ["attack_type",
                     "subtable_name",
                     "number_of_attackers",
                     "percent",
                     "round_num",
                     "extra_bash_arg_1",
                     "extra_bash_arg_2",
                     "extra_bash_arg_3",
                     "extra_bash_arg_4",
                     "extra_bash_arg_5"]
            attrs = [x for x in attrs if x != x_axis_col]
            attr_results = {x: get_data(x) for x in attrs}
            x_axis_results = get_data(x_axis_col)
            if x_axis_pts is not None:
                x_axis_results = [x for x in x_axis_results
                                  if x in x_axis_pts]
            return attr_results, x_axis_results, get_data("adopt_pol")

    def validate_percents(self):
        """Validate percents vs percent iters

        We used to have functionality to have different subtables adopt
        at different percentages. We removed this to make graphing easier
        """

        with Simulation_Results_Table() as db:
            sql = f"SELECT DISTINCT percent, percent_iter FROM {db.name}"
            percents = [x["percent"] for x in db.execute(sql)]
            err_msg = ("We removed functionality to graph different percents"
                       " at different levels due to the deadline")
            assert len(set(percents)) == len(percents), err_msg

    def get_graphs(self, attrs_dict, x_attrs, x_attrs_col, policies_list):
        """Returns every possible graph

        Returns every possible graph
        (consisting of subtable, attack type, and type of graph)
        types of graphs ex: control plane hijacked, etc.
        """

        graphs = []

        # https://stackoverflow.com/a/798893/8903959
        attrs_list_of_lists = list(attrs_dict.values())
        # all possible attribute combos
        attrs_combos = list(itertools.product(*attrs_list_of_lists))
        for attr_combo in attrs_combos:
            attr_combo_dict = {x: y for x, y in zip(list(attrs_dict.keys()),
                                                    attr_combo)}
            for graph_type in Graph.get_possible_graph_types():
                graphs.append(Graph(graph_type,
                                    attr_combo_dict,
                                    x_attrs,
                                    x_attrs_col,
                                    policies_list))
        return graphs
