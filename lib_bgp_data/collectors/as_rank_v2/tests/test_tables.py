#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Nicholas Shpetner"]
__credits__ = ["Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

from ....utils.database import Generic_Table_Test
from ..as_rank_v2_parser import AS_Rank_Parser_V2
from ..tables import AS_Rank_V2


@pytest.mark.asrank_parser_v2
class Test_AS_Rank_V2(Generic_Table_Test):
    """Tests AS_Rank_V2"""

    table_class = AS_Rank_V2
