#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the asrank_website_parser.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Nicholas Shpetner", "Abhinna Adhikari"]
__credits__ = ["Nicholas Shpetner", "Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from unittest.mock import patch
import pytest

from ..as_rank_website_parser import AS_Rank_Website_Parser
from ..tables import AS_Rank_Table
from .open_custom_html import open_custom_html


def produce_rows_lst():
    """Helper function that produces a tds_lst as input for
    the _parse_row method in the AS_Rank_Website_Parser class."""

    soup = open_custom_html('')
    rows = soup.findChildren("tr")[1:]
    return rows


@pytest.mark.asrank_website_parser
class TestAS_Rank_Website_Parser:
    """Tests all functions within the AS_Rank_Website_Parser class."""

    def test_format_page_url(self):
        """Tests producing asrank.caida.org urls."""
        page_num = 1
        url = AS_Rank_Website_Parser()._format_page_url(page_num)
        correct_url = 'https://asrank.caida.org/?page_number=1&page_size=1000&sort=rank'
        assert url == correct_url

    def test_total_pages(self):
        """Tests getting the total number of pages of the asrank table.

        Runs total_pages that mocks sel_driver's get_page method to
        get the custom html.
        """
        with patch('lib_bgp_data.collectors.as_rank_website.tests.open_custom_html') as mock_get_page:
            total_pages = AS_Rank_Website_Parser()._total_pages

            # The custom html should have 67599 rows
            assert total_pages == 71

    def test_parse_row(self):
        """Tests that the row is correctly parsed.

        Use custom html to produce the tds_lst to parse.
        """
        rows = produce_rows_lst()
        parsed_rows = [AS_Rank_Website_Parser()._parse_row(row) for row in rows]

        # The row should only have 5 elements that represents the 5 columns#
        for parsed_row in parsed_rows:
            assert len(parsed_row) == 5

            # Each element within the row should be a string
            for elem in parsed_row:
                assert isinstance(elem, str)

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
        1000 rows have been
        successfully added to the database.
        """
        with AS_Rank_Table(clear=True) as _:
            pass
        parser = AS_Rank_Website_Parser()
        page_num = 1
        parser._parse_page(page_num)
        with AS_Rank_Table() as asrank:
            assert 1000 == len(asrank.get_all())

    @pytest.mark.slow(reason="Needs to query website many times")
    def test_run(self):
        """Tests the _run function

        Verify that the function adds the correct amount of rows to db.
        The database should have AS_Rank_Website_Parser()._total_rows
        number of rows.
        """

        parser = AS_Rank_Website_Parser()
        parser._run()
        with AS_Rank_Table() as asrank:
            assert (parser._total_pages-1) * 1000 == len(asrank.get_all())
