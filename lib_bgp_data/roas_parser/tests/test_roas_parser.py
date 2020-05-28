#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the roas_collector.py file.

For speciifics on each test, see the docstrings under each function.
Note that we do NOT test the parse_roas function, because this is
essentially a database operation and is checked in another file
"""

__authors__ = ["Justin Furuness", "Nicholas Shpetner"]
__credits__ = ["Justin Furuness", "Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

from ..roas_parser import ROAs_Parser
from ..roas_parser import ROAs_Collector
from ...database import Database

@pytest.mark.roas_parser
class Test_ROAs_Parser:
    """Tests all functions within the ROAs Parser class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Parser setup and table deleted before every test"""

        self.parser = ROAs_Parser()
        with Database() as _db:
            _db.execute("DROP TABLE IF EXISTS roas;")

    def OFFtest_parse_roas(self):
        """Tests the parse roas function"""

        # Parses the roas
        self.parser.run()
        # Checks that all formatted roas were entered into the db
        with Database() as db:
            roas = db.execute("SELECT * FROM roas")
        json_roas = self.parser._get_json_roas()
        # Zip checks for same length
        for roa, json_roa in zip(roas, json_roas):
            # Checks if they have the same amount of keys
            assert len(roa) == len(json_roa) - 1  # json has one extra key
            # Checks that each value is the same
            for key in json_roa:
                # We don't save this value
                if key not in ["ta", "maxLength"]:
                    assert str(roa[key]) == str(json_roa[key])
                if key == "maxLength":
                    assert str(roa["max_length"]) == str(json_roa[key])
        # Checks that there is an index on the ROAs Table
        with Database() as db:
            sql = "SELECT * FROM pg_indexes WHERE tablename = 'roas'"
            indexes = db.execute(sql)
            # Makes sure that there is an index
            assert len(indexes) > 0

    def OFFtest_get_json_roas(self):
        """Tests the _get_json_roas function of the roas collector.

        This function should return a list of dicts of roas
        """

        # Get the json and get the roas list from it
        roas = self.parser._get_json_roas()
        # Make sure the returned value is a list
        assert isinstance(roas, list)
        # For each item in the list of dicts:
        for roa_dict in roas:
            # Make sure the item is a dictionary
            assert isinstance(roa_dict, dict)
            # Make sure it has the set of keys that we think it does
            assert set(roa_dict.keys()) == {"asn", "prefix", "maxLength", "ta"}
        # Make sure there are more than 10k ROAs
        assert len(roas) > 10000

    def OFFtest_format_roas(self):
        """Tests the _format_roas function of the roas collector."""

        # Get the list of dicts of ROAs
        roas = self.parser._get_json_roas()
        # Format the ROAs into a list of [asn, prefix, max length]
        formatted_roas = self.parser._format_roas(roas)
        # Make sure they have the same amount of ROAs
        assert len(roas) == len(formatted_roas)
        # Check to make sure formatting works for each roa
        for roa, formatted_roa in zip(roas, formatted_roas):
            # Make sure the asn is correct
            assert formatted_roa[0] == [int(s) for s in roa["asn"].split()
                                        if s.isdigit()][0]
            # Checks for the prefix
            assert formatted_roa[1] == roa["prefix"]
            # Checks for the max length
            assert formatted_roa[2] == int(roa["maxLength"])

    def test_warnings(self):
        """Checks deprecation warnings

        Should check that roas_collector.parse_files returns two
        deprecation warnings
        """

        with pytest.deprecated_call():
            # Call parse_roas() for its warning
            self.parser.parse_roas()
            # Make a temporary ROAs_Parser object to test warning in init
            temp = ROAs_Collector()
