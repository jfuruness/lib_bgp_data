#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

from psycopg2.errors import UndefinedTable
from ..tables import ROAs_Table
from ...database import Generic_Table_Test

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_ROAs_Table(Generic_Table_Test):
    """Tests all functions within the mrt announcements class."""

    table_class = ROAs_Table

    def test_create_index(self):
        """Tests the create index function of the ROAs_Table class"""

        # Initializes the table if it doesn't exist
        with ROAs_Table() as db:
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
