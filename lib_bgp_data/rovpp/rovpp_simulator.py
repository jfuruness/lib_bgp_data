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

from .data_point import Data_Point
from .enums import Attack_Types, Non_Default_Policies
from .multiline_tqdm import Multiline_TQDM
from .subtables_base import Subtables
from .tables import Simulation_Results_Table


from ..base_classes import Parser
from ..relationships_parser import Relationships_Parser
from .. import extrapolator_parser as exr

class ROVPP_Simulator(Parser):
    """This class simulates ROVPP.
    In depth explanation at the top of the file
    """

    def _run(self,
             percents=[1],# list(range(5, 31, 5)),
             num_trials=2,
             exr_bash=None,
             seeded=False,
             seed=0,
             seeded_trial=None,
             attack_types=Attack_Types.__members__.values(),
             adopt_policy_types=Non_Default_Policies.__members__.values()):
        """Runs ROVPP simulation.
        In depth explanation at top of module.
        """

        # forces new install of extrapolator
        exr.ROVPP_Extrapolator_Parser(**self.kwargs).install(force=True)

        # Gets relationships table
        Relationships_Parser(**self.kwargs).run()

        # Clear the table that stores all trial info
        with Simulation_Results_Table(clear=True) as _:
            pass

        # Gets the subdivisions of the internet to track
        tables = Subtables(percents)
        tables.fill_tables()

        # All data points that we want to graph
        data_pts = [Data_Point(tables, i, percent, self.csv_dir)
                    for i, percent in enumerate(percents)]

        # We do this so that we can immediatly skip to the deterministic trial
        trials = [seeded_trial] if seeded_trial else list(range(num_trials))

        # The reason we run tqdm off the number of trials
        # And not number of data points is so that someone can input the
        # deterministic trial number and have it jump straight to that trial
        # In addition - the reason we have multiple bars is so that we can
        # display useful stats using the bar

        with Multiline_TQDM(len(trials)) as pbars:
            if seeded and seed != 0:
                random.seed(seed)
            for trial in trials:
                if seeded and seed == 0:
                    random.seed(trial)
                for data_pt in data_pts:
                    data_pt.get_data(exr_bash,
                                     self.kwargs,
                                     pbars,
                                     attack_types,
                                     adopt_policy_types,
                                     seeded)
                pbars.update()

        tables.close()
