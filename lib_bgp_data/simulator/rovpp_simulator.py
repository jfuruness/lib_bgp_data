#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains ROVPP_Simulator which runs attack/defend simulations
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

from .data_point import Data_Point
from .enums import Attack_Types, Non_Default_Policies
from .multiline_tqdm import Multiline_TQDM
from .subtables_base import Subtables
from .tables import Simulation_Results_Table, Leak_Related_Announcements_Table


from ..base_classes import Parser
from ..relationships_parser import Relationships_Parser
from ..bgpstream_website_parser import BGPStream_Website_Parser, Event_Types
from ..mrt_parser import MRT_Parser, MRT_Sources
from ..database import Database
from .. import extrapolator_parser as exr

class ROVPP_Simulator(Parser):
    """This class simulates ROVPP.
    In depth explanation at the top of the file
    """

    def _run(self,
             percents=[1],# list(range(5, 31, 5)),
             num_trials=2,
             exr_bash=None,  # For development only
             seeded_trial=None,
             deterministic=False,
             attack_types=[x for x in Attack_Types.__members__.values()
                           # Not yet implimented
                           if x != Attack_Types.LEAK],
             adopt_policy_types=[x for x in Non_Default_Policies.__members__.values()
                                 # Not in ASPA policies (not yet implimented)
                                 if x.value not in list(range(1024, 2048))],
             redownload_base_data=True):
        """Runs ROVPP simulation.
        In depth explanation at top of module.
        """


        if redownload_base_data:
            # forces new install of extrapolator
            exr.ROVPP_Extrapolator_Parser(**self.kwargs).install(force=True)
            # Gets relationships table
            Relationships_Parser(**self.kwargs)._run()
 
        # Clear the table that stores all trial info
        with Simulation_Results_Table(clear=True) as _:
            pass

        # Gets the subdivisions of the internet to track
        tables = Subtables(percents)
        tables.fill_tables()

        # All data points that we want to graph
        data_pts = [Data_Point(tables, i, percent, self.csv_dir, deterministic)
                    for i, percent in enumerate(percents)]

        # We run tqdm off of the number of scenarios that need to be run. The
        # total number of scenarios is the number of Test objects that are
        # created and run. This allows someone to input the scenario number
        # they see in the tqdm bar and jump to that specifiic scenario. Having
        # the tqdm be based on the number of trials is too slow, and we
        # potentially may have to wait a while for a specific tets to be run
        # in a specific trial. The reason we have multiple bars is so that we
        # can display useful status using the bar.

        # Get total number of scenarios (Test class objects that will be run).
        # This value will be used in the tqdm
        total = 0
        for trial in range(num_trials):
            for data_pt in data_pts:
                for test in data_pt.get_possible_tests(attack_types,
                                                       adopt_policy_types,
                                                       trial,
                                                       set_up=False):
                    total += 1

        with Multiline_TQDM(total) as pbars:
            for trial in range(num_trials):
                for data_pt in data_pts:
                    data_pt.get_data(pbars,
                                     attack_types,
                                     adopt_policy_types,
                                     trial,
                                     exr_bash=exr_bash,
                                     exr_kwargs=self.kwargs
                                     seeded_trial=seeded_trial)
        tables.close()
