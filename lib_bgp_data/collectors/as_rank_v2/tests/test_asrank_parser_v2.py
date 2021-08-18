#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the as_rank_v2_parser.py file.
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

from ..as_rank_v2_parser import AS_Rank_Parser_V2
from ..tables import AS_Rank_V2

@pytest.mark.asrank_parser_v2
class Test_AS_Rank_Parser_V2:

    def test_run(self):
        parser = AS_Rank_Parser_V2()
        parser._run(1, 50)
        with AS_Rank_V2() as db:
            result = db.execute('SELECT count(*) FROM as_rank_v2')
            print(result)
            # Temporary hardcoding
            assert result == 101276
