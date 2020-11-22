#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the blacklist_parser.py file."""

__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

from psycopg2.errors import UndefinedTable
import pytest

from ..blacklist_parser import Blacklist_Parser
from ..tables import Blacklist_Table
from ....database import Database


@pytest.skip(reason="Modified code to be OO for future blacklist sources")
@pytest.mark.blacklist_parser
class Test_Blacklist_Parser:
    """Tests functions within the Blacklist Parser class."""
    @pytest.fixture(autouse=True)
    def setup(self):
        """Parser setup and table deleted before every test"""
        # List of sources:
        self.lists = ['uce2', 'uce3', 'spamhaus', 'mit']
        with Database() as _db:
            _db.execute("DROP TABLE IF EXISTS blacklist")
        self.parser = Blacklist_Parser()

    def test_get_blacklists(self):
        """This test makes sure that all blacklists were recieved and
        that there is some content or data."""
        raw_data = self.parser._get_blacklists()
        for l in self.lists:
            # Make sure we got something
            assert raw_data[l] is not ''
            assert raw_data[l] is not ' '
            assert raw_data[l] is not None
        return raw_data

    def test_parse_lists(self):
        """This test makes sure that the blacklists were parsed
        correctly, i.e. each key's items in dict are a list of strs
        of format ####### instead of AS#######"""
        parsed = self.parser._parse_lists(self.test_get_blacklists())
        for key in parsed:
            for item in parsed[key]:
                assert item.isdigit()
        return parsed

    def test_format_dict(self):
        """This test makes sure that the list before conversion to csv
        is formatted correctly, i.e. a list of [asn, source]"""
        formatted = self.parser._format_dict(self.test_parse_lists())
        for entry in formatted:
            assert type(entry[0]) is str
            assert len(entry[0]) > 0
            assert entry[1] in self.lists
            assert len(entry) == 2
        return formatted

    def test_run(self):
        """Test that should make sure that there are no errors and that
        the table is populated with the correct amount of ASNs"""
        # Run the parser
        self.parser._run()
        # Get the raw data.
        raw_dict = self.test_parse_lists()
        # Get # of ASNs in each source
        raw_sizes = [len(raw_dict[source]) for source in raw_dict]
        table_sizes = []
        with Database() as db:
            # This loop will go through each column and ensure that
            # the column is not empty and save the size of column to
            # table_sizes.
            for l in self.lists:
                # formatting string
                l = "'" + l + "'"
                sql = "SELECT * FROM blacklist WHERE source =" + l
                asn_list = db.execute(sql)
                assert len(asn_list) > 0
                table_sizes.append(len(asn_list))
        # Ensure that # of asns in raw data = size of columns.
        assert raw_sizes == table_sizes
