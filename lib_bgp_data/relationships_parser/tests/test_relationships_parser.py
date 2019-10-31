#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_parser.py file.

For specifics on each test, see the docstrings under each function.
"""


import pytest
from ..relationships_parser import Relationships_Parser
from ...utils import utils, db_connection, Config
import datetime


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
        # Reset download date to assure new tables are downloaded
        config = Config(self.parser.logger)
        config.update_last_date(datetime.date(1, 1, 1))
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

        url, date = self.parser._get_url()
        # Make sure the returned values are a URL string and a datetime date
        assert type(url) == str
        assert type(date) == datetime.date
        # Make sure the correct URL is used and the correct file is downloaded
        api_url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        api_elements = [x for x in utils.get_tags(api_url, 'a')[0]]
        files = [x["href"] for x in api_elements if "bz2" in x["href"]]
        assert url == api_url + files[-1]

    def test__get_urls_agg(self):
        """Tests the _get_urls_agg helper function"""

        # Test for default case (0 months back)
        assert self.parser._get_url()[0] == self.parser._get_urls_agg()[0]
        # Test for arbitrary number of months back
        urls = self.parser._get_urls_agg(5)
        # Make sure there are elements in the list
        assert len(urls) > 0
        # Get start month for files
        curr_year = datetime.datetime.now().year
        cur_month = datetime.datetime.now().month
        start_month = datetime.datetime(curr_year, curr_month, 1)
        # Make sure the URLs are all valid relationships file URLs
        i = 0
        for url in urls:
            assert "bz2" in url
            assert "as-rel" in url
