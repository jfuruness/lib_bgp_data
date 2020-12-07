#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the postgres.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest
import os

from ..postgres import Postgres
from ..database import Database
from ...utils import utils


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

    def test_backup_table(self):
        """Tests backing up a table

        Make sure backup file is made and then deleted after test is complete
        """

        save_path = "/tmp/test_backup.sql.gz"        
        assert os.path.exists(save_path) is False

        with Database() as db:
            db.execute("DROP TABLE IF EXISTS test_table;")

        self._create_test_table()
        Postgres.backup_table("test_table", "test", save_path)
        assert os.path.exists(save_path)

        with Database() as db:
            db.execute("DROP TABLE IF EXISTS test_table;")

        utils.delete_paths(save_path)
        assert os.path.exists(save_path) is False

    def test_restore_table(self):
        """Tests restoring a table

        Make sure that restore is consistent with previous version of table
        """

        save_path = "/tmp/test_backup.sql.gz"
        assert os.path.exists(save_path) is False

        with Database() as db:
            db.execute("DROP TABLE IF EXISTS test_table;")

        self._create_test_table()
        Postgres.backup_table("test_table", "test", save_path)
        assert os.path.exists(save_path)

        with Database() as db:
            data = db.execute("SELECT * FROM test_table;")
            db.execute("DROP TABLE IF EXISTS test_table;")

        Postgres.restore_table('test', save_path)

        with Database() as db:
            assert data == db.execute("SELECT * FROM test_table;")
            db.execute("DROP TABLE IF EXISTS test_table;")

        utils.delete_paths(save_path)
        assert os.path.exists(save_path) is False

########################
### Helper Functions ###
########################

    def _create_test_table(self):
        """Creates a test table that we can use in the test methods"""

        sql = """CREATE UNLOGGED TABLE IF
              NOT EXISTS test_table (
              num int
              );"""

        with Database() as db:
            db.execute(sql)

        sql_input = """INSERT INTO test_table (num)
                    VALUES (5), (10), (15), (20);"""

