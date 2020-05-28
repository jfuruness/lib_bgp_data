#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the extrapolator.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..rovpp_extrapolator_parser import ROVPP_Extrapolator_Parser


@pytest.mark.extrapolator
@pytest.mark.rovpp
class Test_ROVPP_Extrapolator:
    """Tests all local functions within the Extrapolator class."""

    @pytest.mark.skip(reason="New hires, and not finished writing")
    def test_run(self):
        """Tests the run method of the extrapolator.

        Run a system test
        Should also run input validation tests.
        """

        pass

    @pytest.mark.skip(reason="New hires, and not finished writing")
    def test_install(self):
        """Tests that the extrapolator is installed.

        Test if not installed that it installs
        Test that can be installed twice.
        Test that once installed, can run.
        """

        pass
