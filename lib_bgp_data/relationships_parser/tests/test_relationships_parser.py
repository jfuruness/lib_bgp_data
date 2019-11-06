#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_parser.py file.

For specifics on each test, see the docstrings under each function.
"""


import pytest
import validators
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
        # Parses latest file
        self.parser.parse_files()
        with db_connection() as db:
            # Get number of entries in table 'peers'
            peers = db.execute("SELECT * FROM peers")
            # Get number of entries in table 'customer_providers'
            cust_prov = db.execute("SELECT * FROM customer_providers")
        # Make sure peers table is larger than customer_providers
        assert len(peers) > 0 and len(cust_prov) > 0
        # Return these entry counts for other tests
        return len(peers), len(cust_prov)

    def test_parse_files_agg(self):
        """Tests the parse_files_agg function which is used to aggregate
        relationships data across multiple months.
        """

        # Get a value for the number of entries on the peers and
        # customer_providers table for comparison
        peers, cust_prov = self.test_parse_files()
        # Establish a connection with the database
        with db_connection() as db:
            # Clear both tables for testing
            db.execute("DROP TABLE IF EXISTS peers;")
            db.execute("DROP TABLE IF EXISTS customer_providers;")
            # Parse files for an arbitrary number of months back
            self.parser.parse_files(agg_months=2)
            # Get the counts for both tables after parsing
            peers_agg = len(db.execute("SELECT * FROM peers;"))
            cust_prov_agg = \
             len(db.execute("SELECT * FROM customer_providers;"))
        # Make sure parsing multiple months gives more entries than just one
        assert peers_agg > peers and cust_prov_agg > cust_prov

    def test__get_urls(self):
        """Tests the _get_url helper function"""

        # Try getting just the most recent URL
        url = self.parser._get_urls()[0]
        # Make sure the returned value is a valid URL
        assert validators.url(url)
        # Make sure the correct URL is used and the correct file is downloaded
        api_url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        api_elements = [x for x in utils.get_tags(api_url, 'a')[0]]
        files = [x["href"] for x in api_elements if "bz2" in x["href"]]
        assert url == api_url + files[-1]
        # Test for arbitrary number of months back
        urls = self.parser._get_urls(5)
        # Make sure there are elements in the list
        assert len(urls) > 0
        # Make sure the URLs are all valid relationships file URLs
        for url in urls:
            assert validators.url(url)
            assert "as-rel" in url and "bz2" in url
