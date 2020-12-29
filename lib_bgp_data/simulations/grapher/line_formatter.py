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


class Line_Formatter:
    def __init__(self, policies):
        self.policy_format_dict = {}
        marks_styles_colors = self.markers_styles_colors
        for i, policy in enumerate(policies):
            self.policy_format_dict[policy] = Line_Format(marks_styles_colors)

    @property
    def markers_styles_colors(self):
        # We can't use a simple for loop here
        # Since we want them to both change as much as possible
        # so instead we zip together markers and styles
        # with every possible ordering of each
        marker_perms = itertools.permutations(self.markers, len(self.markers))
        style_perms = [self.styles] * len(marker_perms)
        color_perms = tertools.permutations(self.colors, len(self.colors))
        markers = self.flatten_list(marker_perms)
        styles = self.flatten_list(style_perms)
        colors = self.flatten_list(list(color_perms)[::-1])
        return list(zip(markers, styles, colors))

    def get_format_kwargs(self, policy):
        return {"label": policy,
                "ls": self.policy_dict[policy].style,
                "marker": self.policy_dict[policy].marker,
                "color": self.policy_dict[policy].color}

    def flatten_list(self, l):
        return list(itertools.chain.from_iterable(list(l)))

    @property
    def markers(self):
        return [".", "1", "*", "x", "d", "2", "3", "4"]

    @property
    def styles(self):
        return ["-", "--", "-.", ":", "solid", "dotted", "dashdot", "dashed"]

    @property
    def colors(self):
        # https://matplotlib.org/2.0.2/api/colors_api.html
        return ["b", "g", "r", "c", "m", "y", "k", "w"]
