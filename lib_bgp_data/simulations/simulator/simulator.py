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

from .attacks import Attack
from .data_point_info import Data_Point
from .multiline_tqdm import Multiline_TQDM
from .subtables import Subtables
from .tables import Simulation_Results_Table
from ..enums import Non_Default_Policies
from ...collectors import AS_Rank_Website_Parser
from ...collectors.as_rank_website.tables import AS_Rank_Table
from ...collectors import Relationships_Parser
from ...collectors.relationships.tables import ASes_Table
from ...extrapolator import Simulation_Extrapolator_Wrapper as Sim_Exr
from ...utils.base_classes import Parser


class Simulator(Parser):
    """This class simulates Attack defend scenarios on the internet.
    In depth explanation at the top of the file
    """

    def _run(self,
             percents=[1],
             num_trials=2,
             exr_bash=None,  # For development only
             exr_branch=None,  # For development only
             seeded_trial=None,
             deterministic=False,
             attack_types=Attack.runnable_attacks[:1],
             adopt_policies=list(Non_Default_Policies.__members__.values())[:1],
             number_of_attackers=[1],
             extra_bash_args=[None],
             redownload_base_data=False):
        """Runs Attack/Defend simulation.
        In depth explanation at top of module.
        """

        assert number_of_attackers == [1], "No. Just no."

        if redownload_base_data:
            # Download as rank, relationships, extrapolator
            # Separate function for development ease
            self._redownload_base_data(exr_branch)

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
        total = self._total(data_pts,
                            attack_types,
                            number_of_attackers,
                            adopt_policies,
                            num_trials,
                            extra_bash_args)

        with Multiline_TQDM(total) as pbars:
            for trial in range(num_trials):
                for data_pt in data_pts:
                    data_pt.get_data(pbars,
                                     attack_types,
                                     number_of_attackers,
                                     adopt_policies,
                                     trial,
                                     seeded_trial=seeded_trial,
                                     exr_bash=exr_bash,
                                     exr_kwargs=self._exr_kwargs(exr_branch),
                                     extra_bash_args=extra_bash_args)
        tables.close()

    def _redownload_base_data(self, exr_branch):
        """Downloads/creates data, tools, and indexes for simulator

        Tools: Extrapolator with speficied branch
        Data: Relationships data, AS Rank data
        Indexes: ASes_Table, AS_Rank_Table (for creating top_100_ases)
        """

        # forces new install of extrapolator
        Sim_Exr(**self._exr_kwargs(exr_branch)).install(force=True)
        # Gets relationships table
        Relationships_Parser(**self.kwargs)._run()
        # Get as rank data
        AS_Rank_Website_Parser().run(random_delay=True)
        # I don't know which of these are used,
        # But they only take a second to make so for now it will be left
        # They are intended for the join for the top 100 ases
        with ASes_Table() as db:
            db.execute(f"CREATE INDEX ON {db.name}(asn);")
        with AS_Rank_Table() as db:
            for attr in ["asn", "as_rank", "asn, as_rank"]:
                db.execute(f"CREATE INDEX ON {db.name}({attr});")

    def _total(self, data_pts, attack_types, number_of_attackers, adopt_pols, trials, extra_args):
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
                                                   number_of_attackers,
                                                   adopt_pols,
                                                   0,  # trial
                                                   extra_args,
                                                   set_up=False):
                total += trials
        return total

    def _exr_kwargs(self, exr_branch):
        """Gets arguments for the extrapolator"""

        exr_kwargs = self.kwargs
        if exr_branch is not None:
            exr_kwargs["exr_branch"] = exr_branch
        return exr_kwargs
