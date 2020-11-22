#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = ["Justin Furuness, Tony Zheng"]
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from ..tables import Hijacks_Table, Leaks_Table, Outages_Table
from ....utils.database import Generic_Table_Test

class Data_Table_Test(Generic_Table_Test):
    """This class is to be inherited by the other three table testing classes

    It should contain functions for create index and delete duplicates.
    """

    def test_delete_duplicates(self):
        """Tests the delete duplicates function

        Should delete all duplicates from the table.
        Prob insert dummy data to check this.
        """
        with self.table_class() as _db:
            # two identical events are inserted into the table
            sql = f"INSERT INTO {_db.name}(event_number) SELECT(1)"
            _db.execute(sql)
            _db.execute(sql)

            # number of rows
            sql_total = f"SELECT COUNT(*) FROM {_db.name}"
            # number of UNIQUE rows
            sql_unique = f"""SELECT COUNT(*) FROM
                (SELECT DISTINCT event_number FROM {_db.name}) AS temp"""
            total_rows = _db.get_count(sql_total)
            unique_rows = _db.get_count(sql_unique)

            # before deleting duplicates, total should not equal unique
            assert total_rows != unique_rows

            _db.delete_duplicates()
            total_rows = _db.get_count(sql_total)
            unique_rows = _db.get_count(sql_unique)

            # after deleting duplicates total and unique should be the same
            assert total_rows == unique_rows

@pytest.mark.bgpstream_website_parser
class Test_Hijacks_Table(Data_Table_Test):
    table_class = Hijacks_Table

@pytest.mark.bgpstream_website_parser
class Test_Leaks_Table(Data_Table_Test):
    table_class = Leaks_Table

@pytest.mark.bgpstream_website_parser
class Test_Outages_Table(Data_Table_Test):
    table_class = Outages_Table

