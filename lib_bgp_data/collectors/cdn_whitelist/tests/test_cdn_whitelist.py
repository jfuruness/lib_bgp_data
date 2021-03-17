#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the cdn_whitelist.py file.

For speciifics on each test, see the docstrings under each function.
Note that we do NOT test the parse_roas function, because this is
essentially a database operation and is checked in another file
"""

__authors__ = ["Justin Furuness", "Tony Zheng"]
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from os import path
from unittest.mock import patch

from ..cdn_whitelist_parser import CDN_Whitelist_Parser
from ..tables import CDN_Whitelist_Table
from ....utils import utils

@pytest.mark.cdn_whitelist
class Test_CDN_Whitelist:
    """Tests all functions within the ROAs Parser class."""

    @pytest.fixture(autouse=True)
    def parser(self):
        """Parser setup and table deleted before every test"""
        CDN_Whitelist_Table(clear=True)
        return CDN_Whitelist_Parser()

    def test_run(self, parser):
        """Tests the _run function"""

        # Downloads data and inserts into the database 
        # Table should have entries after run
        try:
            parser._run()
            with CDN_Whitelist_Table() as t:
                assert t.get_count() > 0
        # raises runtime error if API returns an error msg
        # likely the API rate limit was hit.
        # happens easily if you run the parser back to back
        except RuntimeError:
            pass

    @patch.object(CDN_Whitelist_Parser, '_get_cdns', return_value=['urfgurf'])
    def test_bad_CDN(self, mock, parser):
        """Tests that an error occurs with a CDN that doesn't exist"""

        with pytest.raises(RuntimeError):
            parser._run()

    def test_get_cdns(self, parser):
        """
        Tests that the CDN organisations are correctly
        being retrieved from the text file.
        """
        test_file = '/tmp/test_cdns.txt'
        utils.delete_paths(test_file)

        with open(test_file, 'w+') as f:
            f.write('IMACDN')

        try:
            assert parser._get_cdns(test_file) == ['IMACDN']
        finally:
            utils.delete_paths(test_file)

    def test_api_limit(self, parser):
        """
        Tests that the parser rejects input files with more than 100 CDNs.
        """

        test_file = '/tmp/test_api_limit.txt'
        with open(test_file, 'w+') as f:
            for i in range(102):
                f.write('TESLA\n')

        try:
            with pytest.raises(AssertionError):
                parser._run(input_file=test_file)
        finally:
            utils.delete_paths(test_file)

