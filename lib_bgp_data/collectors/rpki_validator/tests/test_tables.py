#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pytest

from ..tables import Unique_Prefix_Origins_Table, ROV_Validity_Table
from ....utils.database import Generic_Table_Test

__authors__ = ["Justin Furuness, Tony Zheng"]
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@pytest.mark.rpki_validator
class Test_Unique_Prefix_Origins_Table(Generic_Table_Test):

    table_class = Unique_Prefix_Origins_Table

    # overwrite Generic_Table_Test's test_table_fill
    # it errors because mrt_rpki tabel is not created first
    def test_table_fill(self):
        """Tests fill table function.

        should be able to take in any table name as input
        Should error if table is empty
        Checks distinct
        That's all. Inherited test funcs take care of the rest.
        """
        UPO_table = self.table_class()

        # error if input table is empty
        empty_table = 'an_empty_table'
        UPO_table.execute(f'CREATE TABLE {empty_table} (whatever bigint)')
        with pytest.raises(AssertionError):
            UPO_table.fill_table(empty_table)

        # check distinct
        input_table = 'mrt_rpki'
        sql = f"""CREATE TABLE IF NOT EXISTS {input_table} (
                  origin bigint,
                  prefix cidr
                  );"""
        UPO_table.execute(sql)
        sql = f"""INSERT INTO {input_table} (origin, prefix)
                  VALUES ('1', '192.168.1.0/24')"""
        UPO_table.execute(sql)
        UPO_table.execute(sql) 
        UPO_table.fill_table()
        sql = f'SELECT COUNT(DISTINCT origin) FROM {UPO_table.name}'
        assert UPO_table.get_count() == UPO_table.get_count(sql)

@pytest.mark.rpki_validator
class Test_ROV_Validity_Table(Generic_Table_Test):

    table_class = ROV_Validity_Table

    def test_create_tables(self):
        table = self.table_class()
        table._create_tables()
        # if get_count doesn't error, table exists
        assert table.get_count() >= 0


