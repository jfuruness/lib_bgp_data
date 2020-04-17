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

import os
import random

from tqdm import trange

from .data_point import Data_Point
from .enums import Attack_Types, Non_Default_Policies
from .multiline_tqdm import Multiline_TQDM
from .subtables_base import Subtables
from .tables import Simulation_Results_Table, Attackers_Table, Victims_Table


from ..base_classes import Parser
from ..relationships_parser import Relationships_Parser
from ..relationships_parser.tables import ASes_Table
from ..utils import utils


class ROVPP_Simulator(Parser):
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    def _run(self,
             percents=[1,2,3,4,5,10,20,40,60,80,99],
             num_trials=1,
             exr_bash=None,
             attack_types=Attack_Types.__members__.values(),
             policies=Non_Default_Policies.__members__.values()):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Gets relationships table
        Relationships_Parser(**self.kwargs).parse_files()

        tables = Subtables(percents)
        tables.fill_tables()

        data_pts = [Data_Point(tables, i, p) for i, p in enumerate(percents)]

        # The reason we run tqdm off the number of trials
        # And not number of data points is so that someone can input the
        # deterministic trial number and have it jump straight to that trial
        # In addition - the reason we have multiple bars is so that we can
        # display useful stats using the bar

        with ASes_Table(clear=True) as db:
            db.fill_table()

        # Generate all the tests to run at once
        for trial in trange(num_trials, desc="Generating input"):
            for data_pt in data_pts:
                data_pt.get_possible_tests(attack_types, policies)
                # Note that the thing that takes a while is list rewrites
                # We could initialize the list to a certain size to start
                # But for now that's over optimizing
                # Since this part takes < 5 min and exr takes a day
                # And in addition we could multiprocess it with multi db or whatnot
        attack_rows = []
        victim_rows = []
        for data_pt in data_pts:
            for test in data_pt.tests:
                attack_rows.append(test.attack.attacker_row)
                if test.attack.victim_row is not None:
                    victim_rows.append(test.attack.victim_row)

        for rows, atk_vic_Table in zip([attack_rows, victim_rows],
                                       [Attackers_Table, Victims_Table]):
            csv_path = os.path.join(self.csv_dir, atk_vic_Table.name)
            utils.rows_to_db(rows, csv_path, atk_vic_Table)
        input("!")

        # Store test data
        1/0
        # Run extrapolator - feed as input the policy nums to run
        # inputs normally exr_bash, exr_kwargs, self.percent, pbars
        # Make ribs out table properly


        # Clear the table that stores all trial info
        with Simulation_Results_Table(clear=True) as _:
            pass
        # Probably should do this using multiprocessing
        with Multiline_TQDM(len(trials)) as pbars:
            for test in tests:
                test.analyze_output(tables)
                data_pt.get_data(exr_bash,
                                 self.kwargs,
                                 pbars,
                                 attack_types,
                                 adopt_policy_types,
                                 seeded)
                pbars.update()

        tables.close()
