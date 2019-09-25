#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

from psycopg2.errors import UndefinedTable
from ..tables import ROAs_Table
from ...utils import db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_ROAs_Table:
    """Tests all functions within the mrt announcements class."""

    def test_ROAs_init(self):
        """Tests the _create_tables function of the table.

        called by default when db_connection is run.
        """

        # Initializes the table if it doesn't exist
        with db_connection(ROAs_Table):
            # Initialized correctly
            assert True

    def test_ROAs_table_drop(self):
        """Tests the clear_table function of the table.

        First the table is created, then dropped. All queries should
        return undefined table now.
        """

        # Initializes the table if it doesn't exist
        with db_connection(ROAs_Table) as db:
            # Makes sure that the mrt table is deleted
            db.clear_table()
            try:
                # This should fail
                db.execute("SELECT * FROM roas")
                # If this doesn't fail it's a problem
                assert False
            # Table should be undefined since it was dropped
            except UndefinedTable:
                assert True

    def test_ROAs_table_creation(self):
        """Tests the _create_tables function.

        This needs to be done in this way because the previous test
        did not drop the table before initializing it. First the table
        is initialized if not created, then dropped, then created, and
        then checked to make sure it exists and has no rows.
        """

        # Initializes the table if it doesn't exist
        with db_connection(ROAs_Table) as db:
            # Makes sure that the mrt table is deleted
            db.clear_table()
            # Inits the table when it does not exist
            db._create_tables()
            # Table should exist and have no resuts
            assert db.execute("SELECT * FROM roas") == []

    def test_create_index(self):
        """Tests the create index function of the ROAs_Table class"""

        # Initializes the table if it doesn't exist
        with db_connection(ROAs_Table) as db:
            # Makes sure that the mrt table is deleted
            db.clear_table()
            # Creates the tables from scratch
            db._create_tables()
            # Creates the index
            db.create_index()
            sql = "SELECT * FROM pg_indexes WHERE tablename = 'roas'"
            indexes = db.execute(sql)
            # Makes sure that there is an index
            assert len(indexes) > 0
