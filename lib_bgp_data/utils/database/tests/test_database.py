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


@pytest.mark.database
class Test_Database:
    """Tests all local functions within the Database class."""

    @pytest.mark.skip(reason="New hire work")
    def test_context_manager(self):
        """Tests enter and exit functions

        Test for every combination of having:
            -self._clear
            -clear_table
            -_create_tables
        and make sure output is what you expect
        probably should parametize this function
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_connect(self):
        """Tests connect.

        Try with different cursor factory and check expected output
        Make sure connects to different sections correctly
        Try it with postgres down, should loop
        Should create tables after connects if it has them
        prob should paremetize or split into different funcs
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_execute(self):
        """Tests the database executing

        Should fail if data is not list or tuple
        Should work for data or no data
        Should return a list of dicts, or empty list if none
        prob should paremetize this function
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_multiprocess_execute(self):
        """tests multiprocess execute

        Should execute multiple sql queries at once
        And be faster than just one sql query at once
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_vacuum_analyze_checkpoint(self):
        """Tests vacuum_analyze_checkpoint

        Should make sure all memory that is possible to be freed is freed
        Restarting postgres should not have lots of extra memory
        """
        pass
