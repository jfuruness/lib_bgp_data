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

from unittest.mock import patch
import pytest

from ..asrank_website_parser import ASRankWebsiteParser
from ..tables import ASRankTable
from .open_custom_html import open_custom_html


def produce_tds_lst():
    """Helper function that produces a tds_lst as input for
    the _parse_row method in the ASRankWebsiteParser class."""

    soup = open_custom_html('')
    table = soup.findChildren('table')[0]
    rows = table.findChildren('tr')
    return rows[1].findChildren('td')


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

    def test_produce_url(self):
        """Tests producing asrank.caida.org urls."""

        page_num = 1
        table_rows = 1000
        url = ASRankWebsiteParser()._produce_url(page_num, table_rows)
        correct_url = 'https://asrank.caida.org/?page_number=1&page_size=1000&sort=rank'
        assert url == correct_url

    def test_find_total_rows(self):
        """Tests getting the total number of rows of the asrank table.

        First run _find_total_rows that uses sel_driver's get_page method
        to use selenium driver to dynamically get the html. Also run
        _find_total_rows that mocks sel_driver's get_page method to get the
        custom html.
        """

        total_rows = ASRankWebsiteParser()._find_total_rows()
        assert total_rows > 0

        with patch('lib_bgp_data.asrank_website_parser.selenium_related.sel_driver.SeleniumDriver.get_page') as mock_get_page:
            mock_get_page.side_effect = open_custom_html
            total_rows = ASRankWebsiteParser()._find_total_rows()

            # The custom html should have 67599 rows
            assert total_rows == 67599

    def test_parse_row(self):
        """Tests that the row is correctly parsed.

        Use custom html to produce the tds_lst to parse.
        """

        tds_lst = produce_tds_lst()
        parsed_row = ASRankWebsiteParser()._parse_row(tds_lst)

        # The row should only have 5 elements that represents the 5 columns#
        assert len(parsed_row) == 5

        # Each element within the row should be a string
        for elem in parsed_row:
            assert isinstance(elem) == str

        # The fourth element (country) should only have 2 letters
        assert len(parsed_row[3]) == 2

        # Verify that the elements that should be numbers are numbers
        assert parsed_row[0].isdigit()
        assert parsed_row[1].isdigit()
        assert parsed_row[4].isdigit()

    def test_parse_page(self):
        """Tests that a page from asrank.caida.org is
        successfully added to the db.

        Parse page 1 of asrank.caida.org and then verify that
        ASRankWebsiteParser().rows_per_page have been
        successfully added to the database.
        """

        parser = ASRankWebsiteParser()
        page_num = 1
        parser._parse_page(page_num)
        with ASRankTable() as asrank:
            assert parser.rows_per_page == len(asrank.get_all())

    @pytest.mark.slow(reason="Needs to query website many times")
    def test_run(self):
        """Tests the _run function

        Verify that the function adds the correct amount of rows to db.
        The database should have ASRankWebsiteParser()._total_rows
        number of rows.
        """

        parser = ASRankWebsiteParser()
        parser._run()
        with ASRankTable() as asrank:
            assert parser._total_rows == len(asrank.get_all())
