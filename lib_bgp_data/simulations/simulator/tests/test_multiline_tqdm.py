#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the multiline_tqdm.py file.

For speciifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import inspect
import pytest

from ..multiline_tqdm import Multiline_TQDM
from ..attacks.attack import Attack
from ..attacks.attack_classes import Subprefix_Hijack
from ...enums import Non_Default_Policies


@pytest.mark.simulator
class Test_Multiline_TQDM:
    """Tests all functions within the multiline tqdm class."""

    def test___init___and_close(self):
        """Tests initialization of the Multiline TQDM

        NOTE: please close it after completion
        """

        # Create multiline tqdm object
        ml_tqdm = Multiline_TQDM(total_trials=10)

        # Assert instantiation variables
        assert len(ml_tqdm.pbars) == len(ml_tqdm._get_desc())
        assert ml_tqdm.total_trials == 10
        assert ml_tqdm.current_trial == 0

        for pbar in ml_tqdm.pbars:
            assert pbar.total == 10

        # Close the multiline tqdm object
        ml_tqdm.close()

    def test_context_manager(self):
        """Tests using the multiline tqdm as a context manager"""

        # Create multiline tqdm object using context manager
        with Multiline_TQDM(total_trials=10) as ml_tqdm:

            # Assert instantiaion variables
            assert len(ml_tqdm.pbars) == len(ml_tqdm._get_desc())
            assert ml_tqdm.total_trials == 10
            assert ml_tqdm.current_trial == 0

            # Check instantiation of individual pbars
            for pbar in ml_tqdm.pbars:
                assert pbar.total == 10

    def test_update(self):
        """Tests calling the update func in multiline tqdm.

        make sure that the tqdm bars are all incrimented.
        """

        # Create multiline tqdm object using context manager
        with Multiline_TQDM(total_trials=1) as ml_tqdm:

            # Assert that initial value of each pbar is 0
            for pbar in ml_tqdm.pbars:
                assert pbar.n == 0

            # Update the pbars
            ml_tqdm.update()

            # Assert that the values were actually updated
            assert ml_tqdm.current_trial == 1
            for pbar in ml_tqdm.pbars:
                assert pbar.n == 1

    def test_update_extrapolator(self):
        """Tests calling the update extrapolator func.

        make sure that extrapolator running is changed to false.
        """

        # Create multiline tqdm object using context manager
        with Multiline_TQDM(total_trials=1) as ml_tqdm:

            # Assert that the extraploator-running desccription is True
            ml_tqdm.pbars[-1].desc == "Extrapolator Running: True"

            # Call the set_desc() method, this is necessary for us to be able
            # to call the update_extrapolator() method. We'll pass in 'None'
            # for the args for now
            # https://stackoverflow.com/a/41188411
            params = inspect.signature(Multiline_TQDM.set_desc).parameters
            num_params = len(params)
            # Subtract 2 since we don't need the self and exr_running args
            args = [None for _ in range(num_params-2)]
            ml_tqdm.set_desc(*args)

            # Call the update_extrapolator method and make sure that
            # extrapolator running is changed to False
            ml_tqdm.update_extrapolator()
            ml_tqdm.pbars[-1].desc == "Extrapolator Running: False"
            

    def test_set_desc(self):
        """Tests the set_desc function.

        Parametize this, test with exr running and not
        make sure all text updates properly
        """

        # Create multiline tqdm object using context manager
        with Multiline_TQDM(total_trials=1) as ml_tqdm:

            # Arguments that will be supplied to the set_desc method
            adopt_pol = Non_Default_Policies.BGP
            attack = Subprefix_Hijack("1.2.0.0/16",
                                      "1.2.3.0/24")
            percent = 50
            barg_1 = "barg1"
            barg_2 = "barg2"
            barg_3 = "barg3"
            barg_4 = "barg4"
            barg_5 = "barg5"
            exr_running = True

            # Call set_desc() method
            ml_tqdm.set_desc(adopt_pol,
                             percent,
                             attack,
                             barg_1,
                             barg_2,
                             barg_3,
                             barg_4,
                             barg_5,
                             exr_running)

            # Assert that appropriate variables were instantiated
            assert ml_tqdm.adopt_pol == adopt_pol
            assert ml_tqdm.percent == percent
            assert ml_tqdm.attack == attack
            assert ml_tqdm.extra_bash_arg_1 == barg_1
            assert ml_tqdm.extra_bash_arg_2 == barg_2
            assert ml_tqdm.extra_bash_arg_3 == barg_3
            assert ml_tqdm.extra_bash_arg_4 == barg_4
            assert ml_tqdm.extra_bash_arg_5 == barg_5

            # Get the descs that were generated           
            descs = ml_tqdm._get_desc(adopt_pol,
                                      percent,
                                      attack,
                                      barg_1,
                                      barg_2,
                                      barg_3,
                                      barg_4,
                                      barg_5,
                                      exr_running)

            # Assert that each tqdm bar in multiline tqdm object has
            # the appropriate description
            for pbar, desc in zip(ml_tqdm.pbars, descs):
                # When we set a description for a tqdm bar, ": " is added.
                # Need to trim this off when checking for equality
                assert pbar.desc[:-2] == desc

    def test_get_desc(self):
        """Tests the _get_desc function

        Make sure text is returned properly, both for None and real vals
        """

        # Create multiline tqdm object using context manager
        with Multiline_TQDM(total_trials=1) as ml_tqdm:

            # Expected output if no args are supplied to _get_desc()
            expected_none = ["Attack_cls: NoneType                              ",
                             "Adopt Policy:                                     ",
                             "Adoption Percentage:                              ",
                             "Attacker:                                         ",
                             "Victim:                                           ",
                             "Extra_bash_arg_1:                                 ",
                             "Extra_bash_arg_2:                                 ",
                             "Extra_bash_arg_3:                                 ",
                             "Extra_bash_arg_4:                                 ",
                             "Extra_bash_arg_5:                                 ",
                             "Extrapolator Running: True                        "]

            # Expected output if args are supplied to _get_desc()
            expected_real = ["Attack_cls: Subprefix_Hijack                      ",
                             "Adopt Policy: BGP                                 ",
                             "Adoption Percentage: 50                           ",
                             "Attacker: 1.2.3.0/24                              ",
                             "Victim: 1.2.0.0/16                                ",
                             "Extra_bash_arg_1: barg1                           ",
                             "Extra_bash_arg_2: barg2                           ",
                             "Extra_bash_arg_3: barg3                           ",
                             "Extra_bash_arg_4: barg4                           ",
                             "Extra_bash_arg_5: barg5                           ",
                             "Extrapolator Running: False                       "]
 
            # Arguments that will be supplied to the _get_desc() method
            adopt_pol = Non_Default_Policies.BGP
            attack = Subprefix_Hijack("1.2.0.0/16",
                                      "1.2.3.0/24")
            percent = 50
            barg_1 = "barg1"
            barg_2 = "barg2"
            barg_3 = "barg3"
            barg_4 = "barg4"
            barg_5 = "barg5"

            # Check if expected outputs matches actual outputs
            for exp, desc in zip(expected_none, ml_tqdm._get_desc()):
                assert exp == desc

            for exp, desc in zip(expected_real,
                                 ml_tqdm._get_desc(adopt_pol,
                                                   percent,
                                                   attack,
                                                   barg_1,
                                                   barg_2,
                                                   barg_3,
                                                   barg_4,
                                                   barg_5,
                                                   False)):
                assert exp == desc

