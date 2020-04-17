#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the asrank_data.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Abhinna Adhikari"]
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import pytest

from ..asrank_data import ASRankData


@pytest.mark.asrank_website_parser
class TestASRankData:
    """Tests all functions within the ASRankData class."""
    def __init__(self):
        self._asrank_data = None

    def test_append(self):
        """Tests the insert_data method.

        Insert a previously found list of tds into 
        the class and check expected output.
        """
        self._reset_asrank_data()
        tds_lst = ['',
                   '',
                   '',
                   '',
                   '']
        self._asrank_data.insert_data(tds_lst)
        rows = self._asrank_data._rows
        
        # Check that the length of the _rows is 1
        assert len(rows) == 1

        # Check if the number of entries within the row is 5
        row = rows[0]
        assert len(row) == 5

        #Check that the fourth entry in the row (country) only has 2 chars
        country = row[3]
        assert len(country) == 2

    def test_insert_data_into_db(self):
        """Tests the insert_data_into_db method

        Insert a potential row into db 
        and check expected output.
        """
        self._reset_asrank_data()

    def _reset_asrank_data(self):
        """Creates a new instance so that the data
        within the class is cleared.
        """
        self._asrank_data = ASRankData()
