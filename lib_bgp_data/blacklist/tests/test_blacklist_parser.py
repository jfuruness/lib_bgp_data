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

from ..blacklist_parser import Blacklist_Parser as parser
from ..tables import Blacklist_Table
from ...database import Database

@pytest.mark.blacklist_parser
class Test_Blacklist_Parser:
    """Tests all functions within the Blacklist Parser class."""
    @pytest.fixture(autouse=True)
    def setup(self):
        with Database() as _db:
            _db.execute("DROP TABLE IF EXISTS blacklist")
        

    def test_run(self):
        parser._run(parser)
        with Database() as db:
            asn_list = db.execute("SELECT asn FROM blacklist")
            assert len(asn_list) > 0
