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

from ...utils import utils
from ...utils.database import Database

@pytest.mark.skip(reason="undergrad work")
@pytest.mark.simulator
class Test_Simulator:
    """Tests all functionality that the simulator class offers."""

    def setup(self):
        """Should clear out the entire database every time

        Perhaps use the postgres/database convenience funcs for this?
        """

        pass

    def test_run(self):
        """Tests _run function with default parameters

        All combinations of parameters are not tested
        since that would take too long to be useful"""

        pass

    def test_exr_bash(self):
        """Tests _run function with a different exr_bash

        Should test that exr_bash changes the running of the exr
        probably just echo something
        """

        pass

    def test_deterministic(self):
        """Tests deterministic trials

        Trials should run the same way every time
        """

        pass

    def test_seeded_trial(self):
        """Tests the seeded trial

        Should jump to the trial displayed in the deterministic trial
        """

        pass

    def test_all_scenarios(self):
        """Tests running of all attack types and adopt policies

        percents should be 1, 50, 90. Trials should be 2
        """

        pass

    def test_percents_trials(self):
        """Test with percents as [1, 25, 50, 75, 100] for 4 trials"""

        pass

    def test_redownload_base_data(self):
        """Tests the redownloading of base data function

        Make sure extrapolator is installed and in the correct place
        Parametize this - make sure this works with exr branch or None
        Make sure relationships parser was run
            -to do this, perhaps import tests from relationships parser
        Make sure AS Rank Website Parser was run
            -make sure that there is a random delay
        Make sure ASes Table has an index
        Make sure AS Rank Table has an index
        """

        pass

    def test_total(self):
        """Tests the _total function

        Make sure the total is as expected for a small test case
        """

        pass

    def test_exr_kwargs(self):
        """Test _exr_kwargs function

        Just make sure exr_branch is added if not None
        (test for both None and specified)
        """

        pass
