#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains Simulator which runs attack/defend simulations
See README for in depth explanation
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import random
import uuid

from .attacks import Attack
from .data_point_info import Data_Point
from .multiline_tqdm import Multiline_TQDM
from .subtables import Subtables
from .tables import Simulation_Results_Table
from ..enums import Non_Default_Policies
from ...collectors import AS_Rank_Website_Parser
from ...collectors import Relationships_Parser
from ...collectors import BGPStream_Website_Parser, BGPStream_Website_Event_Types
from ...collectors import MRT_Parser, MRT_Sources
from ...extrapolator import Simulation_Extrapolator_Wrapper
from ...utils.base_classes import Parser
from ...utils.database import Database

class Simulator(Parser):
    """This class simulates Attack defend scenarios on the internet.
    In depth explanation at the top of the file
    """

    def _run(self,
             percents=[1],# list(range(5, 31, 5)),
             num_trials=2,
             exr_bash=None,  # For development only
             seeded_trial=None,
             deterministic=False,
             attack_types=Attack.runnable_attacks[:1],
             adopt_policies=list(Non_Default_Policies.__members__.values())[:1],
             redownload_base_data=True):
        """Runs Attack/Defend simulation.
        In depth explanation at top of module.
        """


        if redownload_base_data:
            # forces new install of extrapolator
            Simulation_Extrapolator_Wrapper(**self.kwargs).install(force=True)
            # Gets relationships table
            Relationships_Parser(**self.kwargs)._run()
            # Get as rank data
            AS_Rank_Website_Parser().run(max_workers=1, random_delay=False)
 
        # Clear the table that stores all trial info
        with Simulation_Results_Table(clear=True) as _:
            pass

        # Gets the subdivisions of the internet to track
        tables = Subtables(percents)
        tables.fill_tables()

        # All data points that we want to graph
        data_pts = [Data_Point(tables, i, percent, self.csv_dir, deterministic)
                    for i, percent in enumerate(percents)]

        # Total number of attack/defend scenarios for tqdm
        total = self._total(data_pts, attack_types, adopt_policies, num_trials)

        with Multiline_TQDM(total) as pbars:
            for trial in range(num_trials):
                for data_pt in data_pts:
                    data_pt.get_data(pbars,
                                     attack_types,
                                     adopt_policies,
                                     trial,
                                     seeded_trial=seeded_trial,
                                     exr_bash=exr_bash,
                                     exr_kwargs=self.kwargs)
        tables.close()

    def _total(self, data_pts, attack_types, adopt_pols, trials):
        """tqdm runs off every possible attack/defend scenario
        This includes: attack type, adopt policy, percent, trial
        This way we can jump to any attack/defend scenario quickly
        Multiline is to display as much info as possible

        Get total number of scenarios (Test class objects that will be run).
        This value will be used in the tqdm
        """
        total = 0
        for data_pt in data_pts:
            for test in data_pt.get_possible_tests(attack_types,
                                                   adopt_pols,
                                                   0,  # trial
                                                   set_up=False):
                total += trials
        return total
