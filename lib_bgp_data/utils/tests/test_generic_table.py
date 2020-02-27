#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

from psycopg2.errors import UndefinedTable
from ...utils import db_connection

__author__ = "Justin Furuness", "Matt Jaccino"
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_Generic_Table:
    def test_table_init(self):
        """Tests the _create_tables function of the table.

        called by default when db_connection is run.
        """

        # Initializes the table if it doesn't exist
        with db_connection(self.table_class) as db:
            pass

    def test_table_drop(self):
        """Tests the clear_tables function of the table.

        First the table is created, then dropped. All queries should
        return undefined table now.
        """

        # Initializes the table if it doesn't exist
        with db_connection(self.table_class) as db:
            # Makes sure that the mrt table is deleted
            db.clear_tables()
            try:
                # This should fail
                db.execute("SELECT * FROM mrt_announcements")
                # If we reach this line it's a failure
                assert False
            # Table should be undefined since it was dropped
            except UndefinedTable:
                pass

    def test_table_creation(self):
        """Tests the _create_tables function.

        This needs to be done in this way because the previous test
        did not drop the table before initializing it. First the table
        is initialized if not created, then dropped, then created, and
        then checked to make sure it exists and has no rows.
        """

        # Initializes the table if it doesn't exist
        with db_connection(self.table_class) as db:
            # Makes sure that the mrt table is deleted
            db.clear_tables()
            # Inits the table when it does not exist
            db._create_tables()
            # Table should exist and have no resuts
            assert db.get_count() == 0

