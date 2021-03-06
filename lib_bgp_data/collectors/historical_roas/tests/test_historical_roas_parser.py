#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the historical_roas_parser.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Tony Zheng"]
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

from ..historical_roas_parser import Historical_ROAS_Parser
from ..tables import Historical_ROAS_Table, Historical_ROAS_Parsed_Table
from ....utils import utils

class Test_Historical_ROAS_Parser:

    @pytest.mark.slow()
    #@pytest.mark.skip()
    def test_clean_run(self):
        """Performs a clean run by dropping the tables."""
        Historical_ROAS_Parsed_Table(clear=True)
        with Historical_ROAS_Table(clear=True) as t:
            Historical_ROAS_Parser().run()
            assert t.get_count() > 1000000

    def test_no_duplicates(self):
        """Tests no duplicates rows exist in the table"""
        with Historical_ROAS_Table() as t:
            sql = f"SELECT DISTINCT({','.join(t.columns[:-1])}) FROM {t.name}"
            distinct = len(t.execute(sql))
            sql = f"SELECT * FROM {t.name}"
            assert len(t.execute(sql)) == distinct

    def test_get_parsed_files(self):
        """
        Tests that the method correctly returns all the rows of
        the parsed files table.
        """
        files = Historical_ROAS_Parser()._get_parsed_files()
        with Historical_ROAS_Parsed_Table() as t:
            for f in files:
                sql = f"SELECT * FROM {t.name} WHERE file = '{f}'"
                assert len(t.execute(sql)) == 1

    def test_add_parsed_files(self):
        """
        Tests that the method correctly adds a new parsed file
        to the parsed files table.
        """
        file_name = 'a_test_file'
        Historical_ROAS_Parser()._add_parsed_files([file_name])
        with Historical_ROAS_Parsed_Table() as t:
            sql = f"SELECT * FROM {t.name} WHERE file = '{file_name}'"
            assert len(t.execute(sql)) == 1
            sql = f"DELETE FROM {t.name} WHERE file = '{file_name}'"
            t.execute(sql)

    def test_reformat_csv(self):
        """
        Tests the reformatting. See the docstring for the method
        for what it does exactly.
        """
        path = '/tmp/test_reformat.csv'
        correct = '37674	41.191.212.0/22	24	'
        correct += '2015-10-30 13:21:35	2016-10-30 13:21:35	.-test_ref\n'

        with open(path, 'w+') as f:
            f.write('A ROW TO BE DELETED\n')
            s = 'willbedeleted,AS37674,41.191.212.0/22,24,'
            s += '2015-10-30 13:21:35,2016-10-30 13:21:35\n'
            f.write(s)

        try:
            Historical_ROAS_Parser()._reformat_csv(path)
            with open(path, 'r') as f:
                assert f.read() == correct
        finally:
            utils.delete_paths(path)
