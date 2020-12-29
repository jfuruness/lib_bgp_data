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


class Line:
    def __init__(self, policy):
        self.policy = policy
        self.x = []
        self.y = []
        self.yerr = []

    def add_data(self, results):
        """results consists of lits of RealDictRows from db

        This adds db data to the line to be graphed
        """

        for result in db.execute(results):
            self.x.append(int(result["percent"]))
            self.y.append(float(result[self.graph_type]) * 100)
            self.yerr.append(
                float(result[self.graph_type + "_confidence"]) * 100)

    def fmt(self, line_formatter):
        return line_formatter.get_format_kwargs(self.policy)
