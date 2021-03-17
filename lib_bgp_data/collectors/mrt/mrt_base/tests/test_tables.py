#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the tables.py file.

For specifics on each test, see the docstrings under each function.
"""

from psycopg2.errors import UndefinedTable
import pytest

from ..tables import MRT_Announcements_Table
from .....utils.database import Generic_Table_Test

__author__ = "Justin Furuness", "Matt Jaccino"
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"


@pytest.mark.mrt_parser
class Test_MRT_Announcements_Table(Generic_Table_Test):
    """Tests all functions within the mrt announcements class.

    Inherits from the test_generic_table class, which will test
    for table creation and dropping the table.
    """

    # Needed for inheritance
    table_class = MRT_Announcements_Table

    @pytest.mark.skip(reason="Should be moved to generic table test")
    def test_IPV_filtering(self):
        """Tests the IPV filtering function of the mrt table class.

        This occurs by first inserting data into an empty table that
        was just initialized. Then we filter by nothing. We check that
        nothing should be removed. then we filter by IPV6 and make sure
        that IPV4 is left. Then we filter by IPV4 and make sure that
        IPV6 is left.

        NOTE: after looking back at this later, this unit test should
        prob be changed to be separate tests for each, which would easily
        be accomplishable with some zipping of some lists, but it's fine
        for now.
        """

        # Initializes the table if it doesn't exist
        with MRT_Announcements_Table() as db:
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
            assert prefixes[0]["prefix"] == "1.2.3.0/24"

            # Reset with new fake data
            db.clear_table()
            db._create_tables()
            self._insert_fake_data(db)

            # Filters by IPV4
            db.filter_by_IPV_family(IPV4=False, IPV6=True)
            prefixes = db.execute("SELECT prefix FROM mrt_announcements")
            # We should only have one IPV6 prefix
            assert prefixes[0]["prefix"] == "2001:db8::/32"

            # Gets ride of test table
            db.clear_table()

    def _insert_fake_data(self, db):
        """Inserts one IPV4 and one IPV6 prefix into the MRT table"""

        _sqls = ["""INSERT INTO mrt_announcements(prefix)
                    VALUES ('1.2.3.0/24')""",
                 """INSERT INTO mrt_announcements(prefix)
                    VALUES ('2001:db8::/32')"""]
        for sql in _sqls:
            db.execute(sql)
