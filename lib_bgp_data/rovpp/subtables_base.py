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


class Subtables:

    def __init__(self, percents, connect=True):

        # Note that if you want to change adoption percentage:
        # Simply change percents to a list of your choosing here

        # Add any extra tables to this initial list
        self.tables = [Subtable(Top_100_ASes_Table,
                                percents,
                                possible_attacker=False),
                       Subtable(Edge_ASes_Table, percents)]
        # Etc table must go at the end. It is all leftover ases
        self.tables.append(Subtable(Etc_ASes_Table,
                                    percents,
                                    possible_attacker=False))

        if connect:
            for table in self.tables:
                table.connect()

    def close(self):
        for table in self.tables:
            table.close()

class Subtable:
    """Subtable that we divide results into"""

    def __init__(self, Table_Class, percents, possible_attacker=True):
        self.Table = Table_Class
        self.possible_attacker = possible_attacker
        self.percents = percents

    def connect(self):
        """Connects table to database"""

        self.Table = self.Table()

    def close(self):
        """Closes connection"""

        self.Table.close()
