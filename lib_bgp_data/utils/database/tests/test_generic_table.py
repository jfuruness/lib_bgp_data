#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the database.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..database import Database

@pytest.mark.skip(reason="New hire work")
@pytest.mark.database
class Test_Generic_Table:
    """Tests all local functions within the Generic_Table class.

    This should be fairly straightforward. Test all convenience funcs.
    Can use it with a table to do it. Only thing is for filter by ip
    family func, you must parametize that function to make sure it works
    for every possible combination
    """

    pass
