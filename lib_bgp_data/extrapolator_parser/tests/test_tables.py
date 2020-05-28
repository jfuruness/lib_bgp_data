#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

import pytest

from ..tables import ROVPP_Extrapolator_Rib_Out_Table
from ...database import Generic_Table_Test

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@pytest.mark.skip(reason="New hires")
@pytest.mark.extrapolator
@pytest.mark.rovpp
class Test_ROVPP_Extrapolator_Ribs_Out_Table(Generic_Table_Test):
    """Tests all functions within the mrt announcements class.

    Inherits from the test_generic_table class, which will test
    for table creation and dropping the table.
    """

    # Needed for inheritance
    table_class = ROVPP_Extrapolator_Rib_Out_Table

    @pytest.mark.skip(reason="new hires")
    def test_fill_table(self):
        """Tests the fill table function

        Run with the following inputs:
            atk and vic prefixes no overlap(multiple of each)
            atk and vic prefixes some overlap (multiple of each)
            atk and vic prefixes complete overlap (multiple)
            atk prefixes (multiple)
            vic prefixes (multiple)

        Make sure output is as expected. Should be ribs out.

        Also make sure that tables are destroyed afterwards
        """
