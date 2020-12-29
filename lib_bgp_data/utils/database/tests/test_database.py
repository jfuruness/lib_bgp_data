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
import time

from psycopg2.extras import *
from ..database import Database
from ..generic_table import Generic_Table
from .fake_table import Fake_Table


@pytest.mark.database
class Test_Database:
    """Tests all local functions within the Database class."""

    def test_context_manager(self):
        """Tests enter and exit functions

        Test for every combination of having:
            -self._clear
            -clear_table
            -_create_tables
        and make sure output is what you expect
        probably should parametize this function
        """
        # We first create the table, make sure the table exists,
        # then check that generic table's clear_table works as expected
        with Fake_Table(clear=True) as fake_table:
            sql = "SELECT * FROM information_schema.tables where table_name='fake' "
            result = fake_table.execute(sql)
            assert result[0]['table_name'] == 'fake'
            fake_table.clear_table()
            result = fake_table.execute(sql)
            assert result == []

    @pytest.mark.parametrize("cursor, typ", [(RealDictCursor, OrderedDict), (DictCursor, list), (NamedTupleCursor, tuple)])
    def test_connect(self, cursor, typ):
        """Tests connect.

        Try with different cursor factory and check expected output
        Make sure connects to different sections correctly
        Try it with postgres down, should loop
        Should create tables after connects if it has them
        prob should paremetize or split into different funcs
        """

        db = Database()
        db._connect(cursor)
        db.execute("CREATE TABLE IF NOT EXISTS fake (test_col int);")
        db.execute("INSERT INTO fake (test_col) VALUES (1), (2), (3);")
        result = db.execute("SELECT * FROM fake")
        assert typ in type(result[0]).__bases__
        db.close()

        # psycopg2.connect.side_effect = psycopg2.OperationalError
        # db._connect(cursor)
        # db.close()

    def test_execute(self):
        """Tests the database executing

        Should fail if data is not list or tuple
        Should work for data or no data
        Should return a list of dicts, or empty list if none
        prob should paremetize this function
        """
        with Fake_Table(clear=True) as fake_table:
            fake_table.execute("INSERT INTO fake (test_col) VALUES (1), (2), (3);")
            result = fake_table.execute("SELECT * FROM fake")
            assert type(result) == (list or tuple)
            assert isinstance(result[0], dict)
            fake_table.execute("DELETE FROM fake")
            result = fake_table.execute("SELECT * FROM fake")
            assert type(result) == list
            assert result == []

    def test_vacuum_analyze_checkpoint(self):
        """Tests vacuum_analyze_checkpoint

        Should make sure all memory that is possible to be freed is freed
        Restarting postgres should not have lots of extra memory
        """
        with Database() as db:
            sql = "SELECT pg_database_size('test');"
            size = db.execute(sql)
            db.vacuum_analyze_checkpoint()
            new_size = db.execute(sql)
            assert new_size[0]['pg_database_size'] < size[0]['pg_database_size']
