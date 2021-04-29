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
             exr_cls=Sim_Exr,  # For development only
             seeded_trial=None,
             deterministic=False,
             attack_types=Attack.runnable_attacks[:1],
             adopt_policies=list(Non_Default_Policies.__members__.values())[:1],
             # These args prob don't change for most cases
             number_of_attackers=[1],
             rounds=1,
             extra_bash_args_1=[None],
             extra_bash_args_2=[None],
             extra_bash_args_3=[None],
             extra_bash_args_4=[None],
             extra_bash_args_5=[None],
             edge_hijack=True,
             etc_hijack=False,
             top_100_hijack=False,
             redownload_base_data=False):
        """Runs Attack/Defend simulation.
        In depth explanation at top of module.
        """

        self._validate_input(num_trials,
                             rounds,
                             number_of_attackers,
                             extra_bash_args_1,
                             extra_bash_args_2,
                             extra_bash_args_3,
                             extra_bash_args_4,
                             extra_bash_args_5)


        if redownload_base_data:
            # Download as rank, relationships, extrapolator
            # Separate function for development ease
            self._redownload_base_data()

        # Clear the table that stores all trial info
        with Simulation_Results_Table(clear=True) as _:
            pass

        # Gets the subdivisions of the internet to track
        tables = Subtables(percents, edge_hijack, etc_hijack, top_100_hijack)
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
                            extra_bash_args_1,
                            extra_bash_args_2,
                            extra_bash_args_3,
                            extra_bash_args_4,
                            extra_bash_args_5)

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
                                     exr_kwargs=self.kwargs,
                                     exr_cls=exr_cls,
                                     rounds=rounds,
                                     extra_bash_args_1=extra_bash_args_1,
                                     extra_bash_args_2=extra_bash_args_2,
                                     extra_bash_args_3=extra_bash_args_3,
                                     extra_bash_args_4=extra_bash_args_4,
                                     extra_bash_args_5=extra_bash_args_5)
        tables.close()

    def _validate_input(self,
                        trials,
                        rounds, 
                        number_of_attackers,
                        extra_bash_args_1,
                        extra_bash_args_2,
                        extra_bash_args_3,
                        extra_bash_args_4,
                        extra_bash_args_5):

        assert trials > 1, "Need at least 2 trials for conf intervals"
        assert rounds >= 1, "Need at least 1 round"

        assert number_of_attackers == [1], "No. Just no."

        for extra_bash_args in [extra_bash_args_1,
                                extra_bash_args_2,
                                extra_bash_args_3,
                                extra_bash_args_4,
                                extra_bash_args_5]:

            assert isinstance(extra_bash_args, list)

            if extra_bash_args != [None]:
                for x in extra_bash_args:
                    assert isinstance(x, int)

    def _redownload_base_data(self, Exr_Cls=Sim_Exr):
        """Downloads/creates data, tools, and indexes for simulator

        Tools: Extrapolator with speficied branch
        Data: Relationships data, AS Rank data
        Indexes: ASes_Table, AS_Rank_Table (for creating top_100_ases)
        """

        # forces new install of extrapolator
        Exr_Cls(**self.kwargs).install(force=True)
        # Gets relationships table
        Relationships_Parser(**self.kwargs)._run()
        # Get as rank data
        AS_Rank_Website_Parser().run(random_delay=True
)
        # Index to speed up Top_100_ASes_Table.fill_table
        # The following indexes were considered:
        # ases(asn), as_rank(asn), as_rank(as_rank), as_rank(asn, as_rank)
        # Analysis concluded any one of the above would be sufficient.
        # Could change in the future if they become useful elsewhere.

        with AS_Rank_Table() as db:
            db.execute(f"CREATE INDEX ON {db.name}(as_rank);")

    def _total(self,
               data_pts,
               attack_types,
               number_of_attackers,
               adopt_pols,
               trials,
               extra_bash_args_1,
               extra_bash_args_2,
               extra_bash_args_3,
               extra_bash_args_4,
               extra_bash_args_5):
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
                                                   extra_bash_args_1,
                                                   extra_bash_args_2,
                                                   extra_bash_args_3,
                                                   extra_bash_args_4,
                                                   extra_bash_args_5,
                                                   set_up=False):
                total += trials
        return total
