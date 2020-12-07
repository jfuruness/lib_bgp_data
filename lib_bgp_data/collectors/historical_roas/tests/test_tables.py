#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = "Tony Zheng"
__credits__ = "Tony Zheng"
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from ..tables import Historical_ROAS_Table
from ....utils.database import Generic_Table_Test


class Test_Historical_ROAS_Table(Generic_Table_Test):

    def test_delete_duplicates(self):
        with Historical_ROAS_Table() as t:
            # two identical events are inserted into the table
            sql = f"""INSERT INTO {t.name} ({','.join(t.columns)})
                      VALUES(13335, '192.168.0.0', 24,
                             '2019-10-16 11:32:19',
                             '2020-10-16 11:32:19',
                             '1999-08-01');"""
            t.execute(sql)
            t.execute(sql)

            # number of rows
            sql_total = f"SELECT COUNT(*) FROM {t.name}"
            # number of UNIQUE rows
            sql_unique = f"""SELECT COUNT(*)
                             FROM
                                (SELECT DISTINCT * 
                                 FROM {t.name}) AS temp;"""

            total_rows = t.get_count(sql_total)
            unique_rows = t.get_count(sql_unique)

            # before deleting duplicates, total should not equal unique
            assert total_rows != unique_rows

            t.delete_duplicates()
            total_rows = t.get_count(sql_total)
            unique_rows = t.get_count(sql_unique)

            # after deleting duplicates total and unique should be the same
            assert total_rows == unique_rows
