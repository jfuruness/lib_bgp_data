#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the blacklist_parser.py file."""

__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import re
from psycopg2.errors import UndefinedTable
import pytest

from ..blacklist_parser import Blacklist_Parser
from ..blacklist_source import Blacklist_Source
from ..tables import Blacklist_Table
from ....utils.database import Database


@pytest.mark.blacklist_parser
class Test_Blacklist_Parser:
    """Tests functions within the Blacklist Parser class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Parser setup and table deleted before every test"""
        # List of sources:
        self.lists = ['UCE1', 'UCE2', 'UCE2_IP', 'UCE3', 'UCE3_IP',
                      'Spamhaus_asndrop', 'Spamhaus_drop',
                      'Spamhaus_edrop', 'MIT_Blacklist']
        with Database() as _db:
            _db.execute("DROP TABLE IF EXISTS blacklist")
        self.parser = Blacklist_Parser()

    def test_get_blacklists(self):
        """This test makes sure that all blacklists were recieved and
        that there is some content or data."""
        all_data = ''
        self.test_run()
        for src in self.lists:
            with Database() as db:
                data = db.execute(f"SELECT source FROM blacklist WHERE source = '{src}'")
                assert data is not None
        with Database() as db:
            all_data = db.execute("SELECT * FROM blacklist")
        return all_data

    def test_inspect_rows(self):
        """This test makes sure that the blacklists were parsed
        correctly, i.e. each ASN is of format ####### or valid 
        IPv4 addr"""
        all_data = self.test_get_blacklists()
        for row in all_data:
            if row['prefix'] is None:
                assert type(row['asn']) == int
            elif row['asn'] is None:
                pre_row = row['prefix']
                assert re.match(r"[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*/[0-9]*", pre_row)
            else:
                raise RuntimeError(f"Formatting error in row {row}" )

    def test_run(self):
        """Test that should make sure that there are no errors"""
        # Run the parser
        self.parser._run()
