#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the asrank_website_parser.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Abhinna Adhikari"]
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import pytest

from ..asrank_website_parser import ASRankWebsiteParser
from ..table import ASRankTable


@pytest.mark.asrank_website_parser
class TestASRankWebsiteParser:
    """Tests all functions within the ASRankWebsiteParser class."""

    def test__init__(self):
        """Tests initialization of the Asrank website parser.
        
        Verify that the asrank table has been cleared. 
        """

        ASRankWebsiteParser().__init__()
        with ASRankTable() as asrank:
            assert asrank.get_count() == 0

    def test_produce_url_page_1_rows_1000(self):
        """Tests producing asrank.caida.org urls."""

        page_num = 1
        table_rows = 1000
        url = ASRankWebsiteParser()._produce_url(page_num, table_rows)
        correct_url = 'https://asrank.caida.org/?page_number=1&page_size=1000&sort=rank'
        assert url == correct_url

    def test_find_total_rows(self):
        """Tests getting the total number of rows of the asrank table."""

        total_rows = ASRankWebsiteParser()._find_total_rows()
        assert total_rows > 0

    @pytest.mark.skip(reason="Still need to do")
    def test_parse_row(self):
        """Tests that the row is correctly parsed."""
        pass
        

    def test_parse_page(self):
        """Tests that a page from asrank.caida.org is 
        successfully added to the db.

        Parse page 1 of asrank.caida.org and then verify that 
        ASRankWebsiteParser().rows_per_page have been 
        successfully added to the database. 
        """

        asrank_parser = ASRankWebsiteParser()
        page_num = 1
        asrank_parser._parse_page(page_num)
        with ASRankTable() as asrank:
            assert asrank_parser.rows_per_page == len(asrank.get_all())

    @pytest.mark.slow(reason="Needs to query and then parse the many pages of the website")
    def test_run(self):
        """Tests the _run function

        Verify that the function adds the correct amount of rows to db.
        The database should have ASRankWebsiteParser()._total_rows
        number of rows.
        """

        asrank_parser = ASRankWebsiteParser()
        asrank_parser._run()
        with ASRankTable() as asrank:
            assert asrank_parser._total_rows == len(asrank.get_all())
