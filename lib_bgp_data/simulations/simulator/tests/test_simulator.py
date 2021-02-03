#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the simulator.py file.

For speciifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..simulator import Simulator
from ..simulator import Simulation_Results_Table
from ..attacks.attack import Attack
from ...enums import Enums
from ...utils import utils
from ...utils.database import Database
from ...utils.postgres import Postgres


@pytest.mark.simulator
class Test_Simulator:
    """Tests all functionality that the simulator class offers."""

    def setup(self):
        """Should clear out the entire database every time

        Perhaps use the postgres/database convenience funcs for this?
        """

        # Postgres.erase_all()

    def test_run(self):
        """Tests _run function with default parameters

        All combinations of parameters are not tested
        since that would take too long to be useful"""

        Simulator._run()

    def test_exr_bash(self):
        """Tests _run function with a different exr_bash

        Should test that exr_bash changes the running of the exr
        probably just echo something
        """
        #TODO: Just use echo, try to capture stdout, confirm it works
        # May error with echo, use try/catch
        Simulator._run(ext_bash.....
        # OK, so ext_bash seems to affect a datapoint in data_point.py, which in get_data will use exr_bash in Parser.run
        # (see line 83)
        # But I don't have any further information beyond that, what am I working with here?

    @pytest.mark.det
    def test_deterministic(self):
        """Tests deterministic trials

        Trials should run the same way every time
        """

        # Copy table, run again, compare copies?
        with Simulation_Results_Table() as table:                
            Simulator._run(deterministic=True)
            run_one = table.get_all()
            table.clear_table()
            Simulator._run(deterministic=True)
            run_two = table.get_all()
            assert run_one == run_two

    def test_seeded_trial(self):
        """Tests the seeded trial

        Should jump to the trial displayed in the deterministic trial
        """

        # Not sure how to use the seeded arg here, either
        # TODO: Should jump to a trial in deterministic

    def test_all_scenarios(self):
        """Tests running of all attack types and adopt policies

        percents should be 1, 50, 90. Trials should be 2
        """

        percents = [1, 50, 90]
        for i in range(0, 2):
            #TODO: Add percents
            Simulator.run(attack_types=Attack.runnable_attacks,
                          adopt_policies=list(Enums.Non_Default_Policies.__members__.values()))

    def test_percents_trials(self):
        """Test with percents as [1, 25, 50, 75, 100] for 4 trials"""

        percents = [1, 25, 50, 75, 100]
        for i in range(0, 4):
            Simulator._run(percents=percents)

    def test_redownload_base_data(self):
        """Tests the redownloading of base data function

        Make sure extrapolator is installed and in the correct place
        Parametize this - make sure this works with exr branch or None
        Make sure relationships parser was run
            -to do this, perhaps import tests from relationships parser
        Make sure AS Rank Website Parser was run
            -make sure that there is a random delay
        Make sure ASes Table has an index
        """
        #TODO: Add Exr_Cls=Sim_Exr to _redownload_base in simulator.py, don't worry after that
        Simulator._redownload_base_data(something)
        with Database() as db:
            # TODO: Import table, don't use hardcoded name
            assert db.execute("FROM as_rank SELECT * ") is not None
            assert db.execute("FROM ases SELECT * ") is not None
            assert db.execute("SELECT tablename, indexname FROM pg_indexes WHERE tablename = as_rank") is not None
            assert db.execute("SELECT tablename, indexname FROM pg_indexes WHERE tablename = ases") is not None

    def test_total(self):
        """Tests the _total function

        Make sure the total is as expected for a small test case
        """

        total = Simulator._total()
        assert Total = 99999
