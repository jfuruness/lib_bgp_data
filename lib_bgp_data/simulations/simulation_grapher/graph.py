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
    def __init__(self,
                 graph_type,
                 attr_combo_dict,
                 x_attrs_list,
                 x_axis_col,
                 policies_list):
        self.graph_type = graph_type
        self.attr_combo_dict = attr_combo_dict
        self.x_attrs_list = x_attrs_list
        self.x_axis_col = x_axis_col
        self.lines = [Line(x) for x in policies_list]

    def get_data(self):
        for line in self.lines:
            line.add_data(self.attr_combo_dict,
                          self.x_attrs_list,
                          self.x_axis_col,
                          self.graph_type)
        return self

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
        # Remove policies that are not graphed
        policies = [Policies(x.value).name for x in policies]
        filtered_lines = [x for x in self.lines if x.policy in policies]
        # If the policies in this combo aren't in sim results, don't graph
        if len(filtered_lines) == 0:
            return

        fig, ax = plt.subplots()
        plt.xlim(min(self.x_attrs_list), max(self.x_attrs_list))
        plt.ylim(0, 100)
        for line in filtered_lines:
            ax.errorbar(line.x, line.y, yerr=line.yerr, **line.fmt(formatter))

        y_label = self._get_y_label(self.graph_type)
        ax.set_ylabel(y_label)
        if self.x_axis_col == "percent":
            x_label = "Percent Adoption"
        else:
            x_label = self.x_axis_col
        ax.set_xlabel(x_label)
        if title:
            ax.set_title(str(self.attr_combo_dict) + f"|{y_label}")
        # Here due to: WARNING: No handles with labels found to put in legend.
        # This is a bug in matplotlib, handles are auto added
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ax.legend()
        plt.tight_layout()
        plt.rcParams.update({"font.size": 14, "lines.markersize": 10})
        self._save_graph(save_path, plt, fig, _format)

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
