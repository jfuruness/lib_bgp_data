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

class Data_Point:
    def __init__(self, subtables, percent_iter, percent):
        self.subtables = subtables
        self.percent_iter = percent_iter
        self.percent = percent

    def get_data(self, seeded, exr_bash, exr_kwargs, pbars):
        for test in self.get_possible_tests(seeded=seeded):
            test.run(self.subtables, exr_bash, exr_kwargs, self.percent, pbars)

    def get_possible_tests(self, set_up=True):
        for scenario in Scenarios.__members__.values():
            # Sets adopting ases, returns hijack
            attack = self.set_up_test(scenario) if set_up else None
            
            for adopt_pol in Non_Default_Policies.__members__.values():
                yield Test(scenario, attack, adopt_pol)

    def set_up_test(self, scenario):
        # Fills the hijack table
        with Hijack_Table(clear=True) as db:
            hijack = db.fill_table(self.tables.possible_hijackers, scenario)
        # Sets the adopting ases
        self.tables.set_adopting_ases(self.percent_iter, hijack.attacker_asn)
        # Return the hijack class
        return hijack
