#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from pathos.multiprocessing import ProcessingPool
from multiprocessing import cpu_count
import sys
from math import sqrt
import matplotlib
# https://raspberrypi.stackexchange.com/a/72562
matplotlib.use('Agg')
from matplotlib.transforms import Bbox
from pathos.threading import ThreadPool
import matplotlib.pyplot as plt
from statistics import mean, variance, StatisticsError
from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
import json
import os
from tqdm import tqdm
from .enums import Non_BGP_Policies, Policies, Non_BGP_Policies, Hijack_Types, Conditions
from .enums import AS_Types, Control_Plane_Conditions as C_Plane_Conds
from .tables import Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table
from .tables import ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table, ROVPP_All_Trials_Table
from ..relationships_parser import Relationships_Parser
from ..relationships_parser.tables import AS_Connectivity_Table
from ..bgpstream_website_parser import BGPStream_Website_Parser

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Input_Subtables(Subtables):
    """Contains subtable functionality for pre exr functions"""

    def __init__(self, percents):
        super(Input_Subtables, self).__init__(percents)
        self.input_tables = [Input_Table(x) for x in self.tables]

    def fill_input_tables(self):
        for subtable in self.input_tables:
            subtable.fill_input_table(self.tables)

    def set_adopting_ases(self, percent_iter, attacker, seeded):
        for subtable in self.input_tables:
            subtable.set_adopting_ases(percent_iter, attacker, seeded)

    def change_routing_policies(self, policy):
        """Changes the routing policy for that percentage of ASes"""

        self.logger.debug("About to change the routing policies")
        for sub_table in self.tables:
            sub_table.change_routing_policies(policy)

    @property
    def possible_hijacker_ases(self):
        possible_hijacker_ases = []
        # For all tables where possible attacker is true
        for _table in self.input_tables:
            possible_hijacker_ases.extend(_table.get_possible_attackers())
        return possible_hijacker_ases


class Input_Subtable(Subtable):
    """Subtable class for ease of use"""

    def set_adopting_ases(self, iteration_num, attacker, deterministic):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker, deterministic)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)

    def get_possible_attackers(self):
        possible_attackers = []
        if self.possible_attacker:
            possible_attackers = [x["asn"] for x in self.input_table.get_all()]
        return possible_attackers
