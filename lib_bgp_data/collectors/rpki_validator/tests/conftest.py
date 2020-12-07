import pytest
from ..tables import Unique_Prefix_Origins_Table

@pytest.fixture(scope='session')
def test_table():
    test_table_name = 'a_test_table'
    with Unique_Prefix_Origins_Table() as _db:
        sql = f'DROP TABLE IF EXISTS {test_table_name}'
        _db.execute(sql)
        sql = f"""CREATE UNLOGGED TABLE {test_table_name} (
                  origin bigint,
                  prefix cidr
                  );"""
        _db.execute(sql)

        # insert a valid and an invalid prefix-origin pair
        # the second is the invalid one
        sql = f"""INSERT INTO {test_table_name} (origin, prefix)
                  VALUES ('0', '58.181.75.0/24'),
                         ('1', '58.181.75.0/24')"""
        _db.execute(sql)
    return test_table_name

