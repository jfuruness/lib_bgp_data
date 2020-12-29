#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Fake Table

This table inherits from Generic Table and gives itself a name so that
functions and initalization of Generic Table will work correctly."""

__authors__ = ["Nicholas Shpetner"]
__credits__ = ["Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

from ..generic_table import Generic_Table


class Fake_Table(Generic_Table):
    """Fake Table class"""
    __slots__ = []

    name = "fake"
    columns = ["test_col"]

    def _create_tables(self):
        """Creates table if it does not exist"""
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS fake (
            test_col integer) ;"""
        self.execute(sql)

    def _add_data(self):
        """Adds some data into table, for testing purposes"""
        self.execute("INSERT INTO fake (test_col) VALUES (1), (2), (3);")
