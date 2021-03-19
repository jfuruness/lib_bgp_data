#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Abhinna Adhikari"]
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import pytest

from ....utils.database import Generic_Table_Test
from ..tables import AS_Rank_Table


@pytest.mark.asrank_website_parser
class Test_AS_Rank_Table(Generic_Table_Test):
    """Tests AS_Rank_Table."""

    table_class = AS_Rank_Table
