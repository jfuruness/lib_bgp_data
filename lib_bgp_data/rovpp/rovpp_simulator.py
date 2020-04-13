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
from .multiline_tqdm import Multiline_TQDM
from .subtables import Subtables
from .tables import ROVPP_All_Trials_Table
from ..base_classes import Parser
from ..relationships_parser import Relationships_Parser


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
