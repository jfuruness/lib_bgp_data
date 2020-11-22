#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the sample_selector.py file.

For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"


from subprocess import check_call

import pytest

from ..sample_selector import Sample_Selector
from ..tables import MRT_W_Monitors_Table, Monitors_Table, Control_Monitors_Table
from ...mrt_announcements_parser.tables import MRT_Announcements_Table
from ...database import Database
from ...utils import utils


@pytest.mark.exr_verification_parser
class Test_Sample_Selector:
    """This will test methods of the Sample_Selector class."""

    @pytest.mark.slow
    def test_select_samples(self):
        """This function really only fills the tables

        Ensures that the tables are filled after completion"""

        # Drop all tables, including mrt
        # Run mrt_w_monitors, should fail with assertion error
        # Run sample selector
        # Ensure that all tables are populated
        # Ensure that control monitors has the max amnt

