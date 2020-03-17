#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the bgpstream_website_parser.py file.
For specifics on each test, see docstrings under each function.
"""


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..bgpstream_website_parser import BGPStream_Website_Parser
from ...utils import utils


@pytest.mark.bgpstream_website_parser
class Test_BGPStream_Website_Parser:
    """Tests all local functions within the BGPStream_Website_Parser class."""

    @pytest.mark.slow(reason="Needs to query website many times")
    @pytest.mark.skip(reason="New hire work")
    def test_run(self):
        """Tests _run function

        Should use every possible combination of parameters with your own
        hidden html file and the website. When working with the hidden html
        file, assert that output is exactly what you expect. With the website
        assert that the output is approximately what you expect (for instance,
        more than 0 hijacks, shouldn't have empty fields, etc.
        """

        pass 

    @pytest.mark.skip(reason="New hire work")
    def test_get_rows(self):
        """Tests get rows func

        For real website, hidden file in this dir:
            -gets proper amount of rows
            -subtracts 10 rows if no limit
            -If limit is too high or none, results in rows - 10
            -if limit is lower, make sure it returns proper amount
        NOTE: try using mock to insert your own html. If that doesn't work,
        add a keyword arg to the get rows func.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_parse_row(self):
        """Tests parse row function

        Test with every combination of input from:
        -Every combination of (hijack, leak, outage) (country flag/info)
        -known events dict/ empty known events dict
        -known events dict has item, but different start /end time
        -refresh is true or refresh is false
    
        Should make sure output is as expected
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_get_row_front_page_info(self):
        """Tests the get_row_front_page_info function

        Should insert three different dummy rows and make sure
        that all of them return the desired output. Should also
        try a row with and without contry/flag.
        Prob should parametize this function.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_generate_known_events(self):
        """Tests the generate_known_events function

        Fill hijack, leak, and outage table with dummy info
        Get the dictionary back and make sure all rows are in the dict
        Make sure it doesn't fail if one of the tables is empty either.
        Parametize is prob required.
        """

        pass
