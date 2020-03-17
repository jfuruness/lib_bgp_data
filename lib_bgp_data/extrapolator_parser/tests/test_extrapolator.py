#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the extrapolator.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..extrapolator_parser import Extrapolator_Parser


@pytest.mark.extrapolator
class Test_Extrapolator:
    """Tests all local functions within the Extrapolator class."""

    @pytest.mark.skip(reason="New hires, and not finished writing")
    def test_run(self):
        """Tests the run method of the extrapolator.

        Feed in a relationship data set and small mrt file.
        Should perform a system test where it checks the expected
        output.
        Should also run input validation tests.
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    def test_input_validation(self):
        """Tests the input validation of the extrapolator.

        Try with and without:
        Peers table
        Provider Customers table
        Input table
        Installation.
        (Probably should paremtize this function)
        """

    @pytest.mark.skip(reason="New hires, and not finished writing")
    def test_install(self):
        """Tests that the extrapolator is installed.

        Test if not installed that it installs
        Test that can be installed twice.
        Test that once installed, can run.
        """

        pass
