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
from ...enums import Non_Default_Policies
from ....utils import utils
from ....utils.database import Database
from ....utils.database.postgres import Postgres
from ....collectors.relationships.relationships_parser import Relationships_Parser
from ....collectors.as_rank_website.as_rank_website_parser import AS_Rank_Website_Parser
from ....collectors.as_rank_website.tables import AS_Rank_Table
from ....collectors.relationships.tables import ASes_Table

@pytest.mark.simulator
class Test_Simulator:
    """Tests all functionality that the simulator class offers."""

    def setup(self):
        """Should clear out the entire database every time

        Perhaps use the postgres/database convenience funcs for this?
        """
        Relationships_Parser()._run()
        AS_Rank_Website_Parser()._run()

    def test_run(self):
        """Tests _run function with default parameters

        All combinations of parameters are not tested
        since that would take too long to be useful"""

        exr_bash = self.prep_exr()
        Simulator()._run(redownload_base_data=True, exr_bash=exr_bash)

    def test_exr_bash(self):
        """Tests _run function with a different exr_bash

        Should test that exr_bash changes the running of the exr
        probably just echo something
        """
        #TODO: Just use echo, try to capture stdout, confirm it works
        # May error with echo, use try/catch
        #Simulator._run(
        # OK, so ext_bash seems to affect a datapoint in data_point.py, which in get_data will use exr_bash in Parser.run
        # (see line 83)
        # But I don't have any further information beyond that, what am I working with here?

    def test_deterministic(self):
        """Tests deterministic trials

        Trials should run the same way every time
        """

        exr_bash = self.prep_exr()
        # Copy table, run again, compare copies?
        with Simulation_Results_Table() as table:                
            Simulator()._run(deterministic=True, redownload_base_data=False, exr_bash=exr_bash)
            run_one = table.get_all()
            table.clear_table()
            Simulator()._run(deterministic=True, redownload_base_data=False, exr_bash=exr_bash)
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
        exr_bash = self.prep_exr()
        percents = [1, 50, 90]
        for i in range(0, 2):
            Simulator().run(attack_types=Attack.runnable_attacks,
                            adopt_policies=list(Non_Default_Policies.__members__.values()),
                            percents=percents,
                            exr_bash=exr_bash)

    def test_percents_trials(self):
        """Test with percents as [1, 25, 50, 75, 100] for 4 trials"""
        exr_bash = self.prep_exr()
        percents = [1, 25, 50, 75, 100]
        for i in range(0, 4):
            Simulator()._run(percents=percents, exr_bash=exr_bash)

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
        Simulator()._redownload_base_data()
        with ASes_Table() as db:
            assert db.execute(f"SELECT * FROM {db.name}") is not None
            assert db.execute(f"SELECT tablename, indexname FROM pg_indexes WHERE tablename = '{db.name}' ;") is not None
        with AS_Rank_Table() as db:
            assert db.execute(f"SELECT * FROM {db.name}") is not None
            assert db.execute(f"SELECT tablename, indexname FROM pg_indexes WHERE tablename = '{db.name}' ;") is not None

    def test_total(self):
        """Tests the _total function

        Make sure the total is as expected for a small test case
        """
        return 0

    ##################
    #Helper functions#
    ##################
    def prep_exr(self):
        cur_db = ''
        with Database() as db:
            cur_db = db.execute('SELECT current_database();')
            cur_db = cur_db[0]['current_database']
            print(cur_db)
        exr_bash = '/usr/bin/rovpp_compat_modifications_extrapolator -v 1 -i 0 -b 0 -a mrt_w_metadata  -t top_100_ases -t edge_ases -t etc_ases --rounds 1 --config-section ' + cur_db
        return exr_bash
 

