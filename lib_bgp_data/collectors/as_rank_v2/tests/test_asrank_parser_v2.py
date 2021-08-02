#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the asrank_website_parser.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Nicholas Shpetner", "Abhinna Adhikari"]
__credits__ = ["Nicholas Shpetner", "Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from unittest.mock import patch
import pytest

from ..as_rank_website_parser import AS_Rank_Website_Parser
from ..tables import AS_Rank_Table

@pytest.mark.asrank_website_parser
class TestAS_Rank_Parser_V2:
