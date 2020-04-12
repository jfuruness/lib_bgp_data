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


class ROVPP_Simulator(Parser):
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """


    def _run(self,
             percents=list(range(5, 31, 5)),
             num_trials=100,
             exr_bash=None,
             seeded=False,
             seeded_trial=None):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Gets relationships table
        Relationships_Parser(**self.kwargs).parse_files()

        # Clear the table that stores all trial info
        with ROVPP_All_Trials_Table(clear=True) as _:
            pass

        tables = Subtables(percents, seeded)
        tables.fill_tables()

        data_pts = [Data_Point(tables, i, p) for i, p in enumerate(percents)]

        assert deterministic_trial <= num_trials, "Bruh you can't do that"

        # We do this so that we can immediatly skip to the deterministic trial
        trials = [seeded_trial] if seeded_trial else list(range(num_trials))

        # The reason we run tqdm off the number of trials
        # And not number of data points is so that someone can input the
        # deterministic trial number and have it jump straight to that trial
        # In addition - the reason we have multiple bars is so that we can
        # display useful stats using the bar

        with Multiline_TQDM(len(trials)) as pbars:
            for trial in trials:
                if seeded:
                    random.seed(trial)
                for data_pt in data_pts:
                    data_pt.get_data(seeded, exr_bash, self.kwargs, pbars)
                pbars.update()

        tables.close()



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

class Test:
    def __init__(self, scenario, attack, adopt_policy, subtables):
        self.scenario = scenario
        self.attack = attack
        self.adopt_policy = adopt_policy

    def run(self, subtables, exr_bash, exr_kwargs, percent, pbars):
        """Simulates a test:

        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.scenario, self.adopt_policy, percent, self.attack)
        # Changes routing policies for all subtables
        subtables.change_routing_policies(self.adopt_policy)
        # Runs the rov++ extrapolator
        ROVPP_Extrapolator_Parser(**exr_kwargs).run(tables.names, exr_bash)
        # Stores the run's data
        subtables.store(self.attack, self.scenario, self.adopt_policy, percent)
