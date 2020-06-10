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
from ...database import Database


@pytest.mark.blacklist_parser
class Test_Blacklist_Parser:
    """Tests functions within the Blacklist Parser class."""
    @pytest.fixture(autouse=True)
    def setup(self):
        """Parser setup and table deleted before every test"""
        self.parser = Blacklist_Parser()
        # List of sources:
        self.lists = ['uce2', 'uce3', 'spamhaus', 'mit']
        with Database() as _db:
            _db.execute("DROP TABLE IF EXISTS blacklist")

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
            

    def test_run(self):
        """Test that should make sure that there are no errors and that
        the table is populated with the correct amount of ASNs"""
        # Run the parser
        self.parser.run()
        # Get the raw data. Done right after running parser for
        # better precision.
        raw_dict = (self.parser._parse_lists(
                     self.parser._get_blacklists()))
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
        # This has/will fail(ed) sometimes, but that is due to
        # data provider inconsistencies/updates, from what I know.
        errstring = 'This may fail due to source inconsistency.'
        assert raw_sizes == table_sizes, errstring
