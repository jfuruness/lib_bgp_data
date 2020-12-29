#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

import os
import sys
import warnings

import matplotlib
import matplotlib.pyplot as plt
import tikzplotlib

from .enums import Measurement_Types, Graph_Formats
from .line import Line
from .line_formatter import Line_Formatter

from ..enums import AS_Types, Policies

__authors__ = ["Justin Furuness", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Graph:
    def __init__(self, graph_type, subtable, attack_type, policies, percents):
        self.graph_type = graph_type
        self.subtable = subtable
        self.attack_type = attack_type
        self.percents = percents
        self.lines = [Line(policy) for policy in policies]

    def get_data(self):
        for line in self.lines:
            line.add_data(self.subtable,
                          self.attack_type,
                          self.percents,
                          self.graph_type)

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
                    save_path,
                    _format,
                    total,
                    title=True):
        self._print_completion_rate(save_path, total)
        fig, ax = plt.subplots()
        # Remove policies that are not graphed
        policies = [Policies(x.value).name for x in policies]
        for line in [x for x in self.lines if x.policy in policies]:
            ax.errorbar(line.x, line.y, yerr=line.yerr, **line.fmt(formatter))

        y_label = self._get_y_label(self.graph_type)
        ax.set_ylabel(y_label)
        ax.set_xlabel("Percent Adoption")
        if title:
            ax.set_title(f"{self.subtable} | {self.attack_type} | {y_label}")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ax.legend()
        plt.tight_layout()
        plt.rcParams.update({"font.size": 14, "lines.markersize": 10})
        self._save_graph(save_path, plt, fig, _format)

    def _print_completion_rate(self, save_path, total):
        graph_path = "/".join(save_path.split("/")[:3])
        # https://stackoverflow.com/a/47930319/8903959
        file_count = sum(len(files) for _, _, files in os.walk(graph_path))
        # https://stackoverflow.com/a/5419488/8903959
        print(f"Writing {file_count}/{total}\r", end="")
        sys.stdout.flush()

    def _get_y_label(self, graph_type):
        if "trace_hijacked" in graph_type:
            return "Data Plane % Hijacked"
        elif "trace_connected" in graph_type:
            return "Data Plane % Successful Connection"
        elif "trace_disconnected" in graph_type:
            return "Data Plane % Disconnected"
        else:
            return "Percent_" + graph_type

    def _save_graph(self, save_path, plt, fig, _format):
        # https://raspberrypi.stackexchange.com/a/72562
        matplotlib.use('Agg')
        plt.rcParams.update({'figure.max_open_warning': 0})
        if _format == Graph_Formats.PNG:
            return plt.savefig(save_path)
        elif _format == Graph_Formats.TIKZ:
            return tikzplotlib.save(save_path)
        else:
            assert False, "Write graph save func here"

        # Close graph to avoid memory errors
        # https://stackoverflow.com/a/21884375/8903959
        plt.cla()
        plt.clf()
        plt.close(fig)

    def get_save_func_for_graph_format(self, _format):
        if _format == Graph_Formats.PNG:
            return plt.savefig
        elif _format == Graph_Formats.TIKZ:
            return tikzplotlib.save
        else:
            assert False, "Write graph save func here"
