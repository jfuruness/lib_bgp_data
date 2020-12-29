#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

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


class Graph:
    def __init__(self, graph_type, subtable, attack_type, policy, percents):
        self.graph_type = graph_type
        self.subtable = subtable
        self.attack_type = attack_type,
        self.policy = policy
        self.percents = percents
        self.lines = [Line(policy) for policy in policies]

    def get_data(self):
        for line in self.lines:
            with Database() as db:
                sql = f"""SELECT * FROM {Simulation_Results_Avg_Table.name}
                      WHERE subtable_name = '{self.subtable}'
                        AND adopt_pol = '{line.policy}'
                        AND attack_type = '{self.attack_type}'
                      ORDER BY percent"""
                results = [x for x in db.execute(sql)
                           if x["percent"] in self.percents]
                line.add_data(results, self.graph_type)

    @staticmethod
    def get_possible_graph_types():
        # Returns possible measurements, and splits by adopting non adopting
        for graph_type in Measurement_Types.__members__.values():
            for as_type in AS_Types.__members__.values():
                name = AS_Types(as_type.value).name.lower()
                yield graph_type.value.format(name)

    def write_graph(self,
                    policies,
                    formatter: Line_Formatter,
                    save_dir,
                    _format,
                    title=True):
        self._print_completion_rate(self)
        fig, ax = plt.subplots()
        # Remove policies that are not graphed
        for line in [x for x in self.lines if x.policy in policies]:
            ax.errorbar(line.x, line.y, yerr=line.yerr, **line.fmt(formatter))

        y_label = self.get_y_label(self.graph_type)
        ax.set_ylabel(self.get_y_label(self.graph_type))
        ax.set_xlabel("Percent Adoption")
        if title:
            ax.set_title(f"{self.subtable} | {self.attack_type} | {y_label}")
        ax.legend()
        plt.tight_layout()
        plt.rcParams.update({"font.size": 14, "lines.markersize": 10})
        self._save_graph(save_dir, plt, fig, _format)

    def _print_completion_rate(self):
        # https://stackoverflow.com/a/47930319/8903959
        file_count = sum(len(files) for _, _, files in os.walk(self.graph_path))
        # https://stackoverflow.com/a/5419488/8903959
        print(f"Writing {file_count}/{total}\r", end="")
        sys.stdout.flush()

    def _save_graph(self, save_dir, plt, fig, _format):
        fname = "_".join(x.policy for x in self.lines) + _format.value
        # Save either as tikz or as png
        save_func = get_save_func_for_graph_format(_format)
        # Save the graph
        save_func(os.path.join(self.get_save_dir(save_dir, tikz), fname))
        # Close graph to avoid memory errors
        plt.close(fig)

    def get_save_func_for_graph_format(self, _format):
        if _format == Graph_Formats.PNG:
            return plt.savefig
        elif _format == Graph_Formats.TIKZ:
            return tikzplotlib.save
        else:
            assert False, "Write graph save func here"

    def get_save_dir
