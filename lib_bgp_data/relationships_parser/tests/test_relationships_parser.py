#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_parser.py file.

For specifics on each test, see the docstrings under each function.
"""


import pytest
from ..relationships_parser import Relationships_Parser
from ...utils import utils, db_connection, Config
import datetime


__author__ = "Matt Jaccino", "Justin Furuness"
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_Relationships_Parser:
    """Tests all functions within the Relationships Parser class."""

    def setup(self):
        """Parser setup"""

        # Initialize Relationships Parser object
        self.parser = Relationships_Parser()

    def test_parse_files(self):
        """Tests the parse files function"""

        # Delete tables from database
        with db_connection() as db:
            db.execute("DROP TABLE IF EXISTS peers")
            db.execute("DROP TABLE IF EXISTS customer_providers")
        # Parses latest file
        self.parser.parse_files()
        with db_connection() as db:
            # Get number of entries in table 'peers'
            peers = db.execute("SELECT * FROM peers")
            # Get number of entries in table 'customer_providers'
            cust_prov = db.execute("SELECT * FROM customer_providers")
        # Make sure peers table is larger than customer_providers
        assert len(peers) > 0 and len(cust_prov) > 0

    def test__get_url(self):
        """Tests the _get_url helper function"""

        url = self.parser._get_urls()[0]
        # Make sure the returned values are a URL string
        assert type(url) == str
        # Make sure the correct URL is used and the correct file is downloaded
        api_url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        api_elements = [x for x in utils.get_tags(api_url, 'a')[0]]
        files = [x["href"] for x in api_elements if "bz2" in x["href"]]
        assert url == api_url + files[-1]

    def test__get_urls_agg(self):
        """Tests the _get_urls_agg helper function"""

        agg_months = 5

        print(self.parser._get_urls())
        print(self.parser._get_urls(agg_months)[0])

        # Test for default case (0 months back)
        assert self.parser._get_urls()[0] == self.parser._get_urls(agg_months)[-1]
        # Test for arbitrary number of months back
        urls = self.parser._get_urls(agg_months)
        # Make sure there are the right amount of urls in the list
        assert len(set(urls)) == agg_months + 1
        # Make sure the URLs are all valid relationships file URLs
        for url in urls:
            assert "bz2" in url and "as-rel" in url
