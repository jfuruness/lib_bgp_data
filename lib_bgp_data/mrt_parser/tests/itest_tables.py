#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

from psycopg2.errors import UndefinedTable
from ..tables import MRT_Announcements_Table
from ...utils import Database, error_catcher, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_MRT_Announcements_Table:
    """Tests all functions within the mrt announcements class."""

    def test_mrt_announcements_init(self):
        """Tests the _create_tables function of the table.

        called by default when db_connection is run.
        """

        # Initializes the table if it doesn't exist
        with db_connection(MRT_Announcements_Table) as db:
            # Initialized correctly
            assert True 

    def test_mrt_announcements_table_drop(self):
        """Tests the clear_table function of the table.

        First the table is created, then dropped. All queries should
        return undefined table now.
        """

        # Initializes the table if it doesn't exist
        with db_connection(MRT_Announcements_Table) as db:
            # Makes sure that the mrt table is deleted
            db.clear_table()
            try:
                # This should fail
                db.execute("SELECT * FROM mrt_announcements")
                # If this doesn't fail it's a problem
                assert False
            # Table should be undefined since it was dropped
            except UndefinedTable:
                assert True

    def test_mrt_announcements_table_creation(self):
        """Tests the _create_tables function.

        This needs to be done in this way because the previous test
        did not drop the table before initializing it. First the table
        is initialized if not created, then dropped, then created, and
        then checked to make sure it exists and has no rows.
        """

        # Initializes the table if it doesn't exist
        with db_connection(MRT_Announcements_Table) as db:
            # Makes sure that the mrt table is deleted
            db.clear_table()
            # Inits the table when it does not exist
            db._create_tables()
            # Table should exist and have no resuts
            assert db.execute("SELECT * FROM mrt_announcements") == []

    def test_IPV_filtering(self):
        """Tests the IPV filtering function of the mrt table class.

        This occurs by first inserting data into an empty table that
        was just initialized. Then we filter by nothing. We check that
        nothing should be removed. then we filter by IPV6 and make sure
        that IPV4 is left. Then we filter by IPV4 and make sure that
        IPV6 is left.
        """

        # Initializes the table if it doesn't exist
        with db_connection(MRT_Announcements_Table) as db:
            # Makes sure that the mrt table is deleted
            db.clear_table()
            # Creates the tables from scratch
            db._create_tables()
            # Insert one IPV4 and one IPV6 prefix
            self._insert_fake_data(db)
            # Filter by nothing
            db.filter_by_IPV_family(IPV4=True, IPV6=True)
            prefixes = db.execute("SELECT prefix FROM mrt_announcements")
            # Nothing was filtered so the table should be unchanged
            assert len(prefixes) == 2

            # Filter by IPV6
            db.filter_by_IPV_family(IPV4=True, IPV6=False)
            prefixes = db.execute("SELECT prefix FROM mrt_announcements")
            # There should only be the IPV4 prefix left
            assert len(prefixes) == 1
            # There should only be the IPV4 prefix left
            assert prefixes[0]["prefix"] == "1.2.3.0/24"

            # Reset with new fake data
            db.clear_table()
            db._create_tables()
            self._insert_fake_data(db)

            # Filters by IPV4
            db.filter_by_IPV_family(IPV4=False, IPV6=True)
            prefixes = db.execute("SELECT prefix FROM mrt_announcements")
            # We should only have one IPV6 prefix
            assert len(prefixes) == 1
            assert prefixes[0]["prefix"] == "2001:db8::/32"

            # Gets ride of test table
            db.clear_table()
 
    def _insert_fake_data(self, db):
        """Inserts one IPV4 and one IPV6 prefix into the MRT table"""

        sqls = ["""INSERT INTO mrt_announcements(prefix)
                    VALUES ('1.2.3.0/24')""",
                    """INSERT INTO mrt_announcements(prefix)
                    VALUES ('2001:db8::/32')"""]
        for sql in sqls:
            db.execute(sql)
