#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_parser.py file.
For specifics on each test, see the docstrings under each function.
"""


import datetime

import pytest
import validators

from ..relationships_parser import Relationships_Parser
from ...database import Database
from ...utils import utils



__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@pytest.mark.relationships_parser
class Test_Relationships_Parser:
    """Tests all functions within the Relationships Parser class."""

    def setup(self):
        """Parser setup"""

        # Initialize Relationships Parser object
        self.parser = Relationships_Parser()

    def test_parse_files(self, agg_months=0):
        """Tests the parse files function"""

        # Delete tables from database
        with Database() as db:
            db.execute("DROP TABLE IF EXISTS peers")
            db.execute("DROP TABLE IF EXISTS provider_customers")
            # Parses latest file
            self.parser.run(agg_months)
            # Get number of entries in table 'peers'
            _peers = db.execute("SELECT * FROM peers")
            # Get number of entries in table 'provider_customers'
            _cust_prov = db.execute("SELECT * FROM provider_customers")
            # Make sure peers table is larger than provider_customers
        assert len(_peers) > 0 and len(_cust_prov) > 0
        # Return these entry counts for other tests
        return len(_peers), len(_cust_prov)

    def test__get_urls(self):
        """Tests the _get_url helper function"""

        # Try getting just the most recent URL
        url = self.parser._get_urls()[0]
        # Make sure the returned value is a valid URL
        assert validators.url(url)
        # Make sure the correct URL is used and the correct file is downloaded
        api_url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        api_elements = [x for x in utils.get_tags(api_url, 'a')]
        files = [x["href"] for x in api_elements if "bz2" in x["href"]]
        assert url == api_url + files[-1]

    def test__get_urls_agg(self):
        """Tests the _get_urls_agg helper function"""

        agg_months = 5

        # Test for default case (0 months back)
        assert self.parser._get_urls()[0] == self.parser._get_urls(agg_months)[-1]
        # Test for arbitrary number of months back
        urls = self.parser._get_urls(agg_months)
        # Make sure there are the right amount of urls in the list
        assert len(set(urls)) == agg_months + 1
        # Make sure the URLs are all valid relationships file URLs
        for url in urls:
            assert "bz2" in url and "as-rel" in url and validators.url(url)
