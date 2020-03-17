#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from psycopg2.errors import UndefinedTable
import pytest

from ..tables import ROAs_Table
from ...database import Generic_Table_Test

@pytest.mark.roas_parser
class Test_ROAs_Table(Generic_Table_Test):
    """Tests all functions within the mrt announcements class."""

    table_class = ROAs_Table
