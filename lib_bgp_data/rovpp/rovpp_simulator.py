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
             seed=uuid.getnode(),
             seeded_trial=None,
             deterministic=False,
             attack_types=Attack_Types.__members__.values(),
             adopt_policy_types=Non_Default_Policies.__members__.values(),
             redownload_base_data=True,
             redownload_leak_data=True):
        """Runs ROVPP simulation.
        In depth explanation at top of module.
        """

        if redownload_base_data:
            # forces new install of extrapolator
            exr.ROVPP_Extrapolator_Parser(**self.kwargs).install(force=True)
            # Gets relationships table
            Relationships_Parser(**self.kwargs)._run()
 

        if Attack_Types.LEAK in attack_types and redownload_leak_data:
            # Download hijack data if not done already
            BGPStream_Website_Parser(**self.kwargs)._run(
                data_types=[Event_Types.LEAK.value])
            # Download mrt data if not done already
#            MRT_Parser(**self.kwargs)._run(sources=[MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS])
#            with Leak_Related_Announcements_Table(clear=True) as db:
#                db.fill_table()

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
                    data_pt.get_data(exr_bash,
                                        self.kwargs,
                                        pbars,
                                        attack_types,
                                        adopt_policy_types,
                                        trial,
                                        seeded_trial)
        tables.close()
