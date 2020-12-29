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
import os

from psycopg2 import errors
from .fake_table import Fake_Table
from ..database import Database


@pytest.mark.database
class Test_Generic_Table:
    """Tests all local functions within the Generic_Table class.

    This should be fairly straightforward. Test all convenience funcs.
    Can use it with a table to do it. Only thing is for filter by ip
    family func, you must parametize that function to make sure it works
    for every possible combination
    """

    def test_get_all(self):
        """Tests get_all, should return a list with three entries."""
        with Fake_Table(clear=True) as fake_table:
            fake_table._add_data()
            result = fake_table.get_all()
            assert len(result) == 3
            assert type(result) == list

    def test_get_count(self):
        """Tests get count. Should return 3 for 3 rows."""
        with Fake_Table(clear=True) as fake_table:
            fake_table._add_data()
            assert fake_table.get_count() == 3

    def test_clear_table(self):
        """Tests clear_table. Should clear the table,
        then have get_all return a list with nothing in it."""
        with Fake_Table(clear=True) as fake_table:
            fake_table._add_data()
            assert len(fake_table.get_all()) == 3
            fake_table.clear_table()
            with pytest.raises(errors.UndefinedTable):
                fake_table.get_all()

    @pytest.mark.xfail(reason='Insufficent permissions')
    def test_copy_table(self):
        """Tests copy table"""
        with Fake_Table(clear=True) as fake_table:
            fake_table._add_data()
            cwd = os.getcwd()
            cwd += '/test_copy.csv'
            fake_table.copy_table(cwd)

    def test_columns(self):
        """Tests columns"""
        with Fake_Table(clear=True) as fake_table:
            assert fake_table.columns == ['test_col']
