#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the postgres.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..postgres import Postgres


@pytest.mark.database
class Test_Postgres:
    """Tests all local functions within the Postgres class."""

    @pytest.mark.skip(reason="New hire work")
    def test_erase_all(self):
        """Tests erasing all database and config sections"""

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_install(self):
        """Tests install.

        Should generate a random password, add a config section,
        create and mod db. Just check general creation.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_create_database(self):
        """Tests the database creation

        Should create a new database with nothing in it
        Should create a new user
        Should have installed btree_gist extension
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_modify_database(self):
        """tests modifying the database

        Tests modifying the database for speed
        Assert that each line is true in the sql cmds.
            NOTE: you can use the show command in sql
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_unhinge_db(self):
        """Tests unhinging database

        Assert that each line in the sql cmds is true
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_rehinge_db(self):
        """Tests rehinging database

        Assert that each line in the sql cmds is true
        """
        
        pass

    @pytest.mark.skip(reason="New hire work")
    def test_restart_postgres(self):
        """Tests restartng postgres

        Make sure postgres temporarily goes offline then restarts.
        """

        pass
