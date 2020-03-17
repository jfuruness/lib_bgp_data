#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from psycopg2.errors import UndefinedTable
import pytest


class Generic_Table_Test:

    """Base class for all table unit tests

    Note that you can use __test__ = False,
    but then subclass will need to include __test__ = True.
    To avoid user error when extending this package, this was
    renamed to Generic_Table_Test so as not to be caught by pytest.
    """

    def test_table_init(self):
        """Tests the _create_tables function of the table.

        called by default when db_connection is run.
        """

        # Initializes the table if it doesn't exist
        with self.table_class() as _:
            pass

    def test_table_drop(self):
        """Tests the clear_tables function of the table.

        First the table is created, then dropped. All queries should
        return undefined table now.
        """

        # Initializes the table if it doesn't exist
        with self.table_class() as _db:
            # Makes sure that the mrt table is deleted
            _db.clear_table()
            try:
                # This should fail
                _db.get_all()
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
        with self.table_class() as _db:
            # Makes sure that the mrt table is deleted
            _db.clear_table()
            # Inits the table when it does not exist
            if hasattr(_db, "_create_tables"):
                _db._create_tables()
                # Table should exist and have no resuts
                assert _db.get_count() == 0

    # Marked slow because sometimes it will be
    @pytest.mark.slow
    def test_table_fill(self):
        """Tests the fill_tables function.

        This needs to be done in this way because the previous test
        did not drop the table before initializing it. First the table
        is initialized if not created, then dropped, then created, and
        then checked to make sure it exists and has no rows.
        """

        # Initializes the table if it doesn't exist
        with self.table_class() as _db:
            # Makes sure that the mrt table is deleted
            _db.clear_table()
            # Inits the table when it does not exist
            if hasattr(_db, "_create_tables"):
                _db._create_tables()
                # Table should exist and have no resuts
                assert _db.get_count() == 0

            if hasattr(_db, "fill_table"):
                _db.fill_table()
                assert _db.get_count() > 0

    # Marked slow because sometimes it will be
    @pytest.mark.slow
    def test_create_index(self):
        """Tests index creation"""

        with self.table_class() as _db:
            if hasattr(_db, "create_index"):
                _db.clear_table()
                _db._create_tables()
                _db.create_index()
                sql = f"""SELECT * FROM pg_indexes
                      WHERE tablename = '{_db.name}'"""
                indexes = _db.execute(sql)
                assert len(indexes) > 0
