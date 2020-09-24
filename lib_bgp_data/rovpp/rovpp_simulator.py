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
             exr_bash=None,
             seeded=False,
             seed=0,
             seeded_trial=None,
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

        # prints all leaks with loops in them
        with Database() as db: 
            prepending = set()
            loops = set()
            leaked_to_many = set()
            leaked_to_one = set()
            leaks = db.execute("SELECT * FROM leaks;")
            for leak in leaks:
                if len(leak["leaked_to_number"]) == 1:
                    leaked_to_one.add(leak["url"].replace("/event/", ""))
                else:
                    leaked_to_many.add(leak["url"].replace("/event/", ""))
                cur_path = set()
                for _as in leak["example_as_path"]:
                    if _as in cur_path:
                        if _as != prev_as:
                            loops.add(leak["url"].replace("/event/", ""))
                        else:
                            prepending.add(leak["url"].replace("/event/", ""))
                        break
                    cur_path.add(_as)
                    prev_as = _as
        print("prepending = " + str(prepending))
        print(len(prepending))
        print("loops = " + str(loops))
        print(len(loops))
        print("multileak = " + str(leaked_to_many))
        print(len(leaked_to_many))
        print("single_leak = " + str(leaked_to_one))
        print(len(leaks))
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
                                     seeded,
                                     trial)
                pbars.update()

        tables.close()
