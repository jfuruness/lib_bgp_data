#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the data_classes.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness, Tony Zheng"]
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup as Soup
from ..data_classes import Data, Hijack, Leak, Outage
from ..tables import Hijacks_Table, Leaks_Table, Outages_Table
from ..event_types import BGPStream_Website_Event_Types
from itertools import combinations
from .create_HTML import HTML_Creator
# Importing actually runs the tests
#from .test_tables import Test_Hijacks_Table, Test_Leaks_Table, Test_Outages_Table


class Test_Data:
    """Tests all functions within the Data class.

    NOTE: You may want to make this not a test class
    and simply have all other classes inherit it."""

    @staticmethod
    def init(event):
        type_ = event['event_type']
        if type_ == BGPStream_Website_Event_Types.HIJACK.value:
            return Hijack('/tmp/')
        if type_ == BGPStream_Website_Event_Types.LEAK.value:
            return Leak('/tmp/')
        if type_ == BGPStream_Website_Event_Types.OUTAGE.value:
            return Outage('/tmp/')

    @staticmethod
    def uncommon_info(event):
        type_ = event['event_type']
        if type_ == BGPStream_Website_Event_Types.HIJACK.value:
            return ['expected_origin_name', 'expected_origin_number',
                    'detected_origin_name', 'detected_origin_number',
                    'expected_prefix', 'more_specific_prefix',
                    'detected_as_path', 'detected_by_bgpmon_peers']

        if type_ == BGPStream_Website_Event_Types.LEAK.value:
            return ['origin_as_name', 'origin_as_number',
                    'leaker_as_name', 'leaker_as_number',
                    'leaked_prefix', 'leaked_to_number', 'leaked_to_name',
                    'example_as_path', 'detected_by_bgpmon_peers']

        if type_ == BGPStream_Website_Event_Types.OUTAGE.value:
            return ['as_name', 'as_number',
                    'number_prefixes_affected', 'percent_prefixes_affected']

    def test_append(self, setup):
        """Tests the append function

        Should have input for every combo of:
            -hijack, leak, outage
            -country info vs non country info
        And check expected output.
        """
        for event in setup.events:
            data = Test_Data.init(event)
            with patch('lib_bgp_data.utils.utils.get_tags') as mock:
                mock.side_effect = setup.open_custom_HTML
                data.append(event['row'])

            # Columns are retrieved from the Postgres table columns
            # which has an 'id' column used as the primary key.
            # Not part of row data, so must be removed 
            cols = data._columns
            cols.remove('id')
 
            for i, c in enumerate(cols):
                assert data.data[0][i] == event[c]

    def test_db_insert(self, setup):
        """Tests the db_insert function

        Should have input with the powerset of all the combinations of:
            -hijack, leak, outage
            -country info vs non country info
        And check expected output.
        """
        for event in setup.events:
            data = Test_Data.init(event)
            # need something to insert
            with patch('lib_bgp_data.utils.utils.get_tags') as mock:               
                mock.side_effect = setup.open_custom_HTML                
                data.append(event['row']) 

            with data.table() as t:
                for IPV4, IPV6 in combinations([True, False], 2):
                    data.db_insert(IPV4, IPV6)
                    
                    # db_insert creates indexes
                    sql = f"""SELECT * FROM pg_indexes
                              WHERE indexname = '{t.name}_index'"""
                    assert len(t.execute(sql)) == 1

                    # db_insert deletes duplicates
                    sql = f"SELECT DISTINCT * FROM {t.name}"
                    assert t.get_all() == t.execute(sql) 

                    # check IPV filtering was successful
                    for IPV, num in zip([IPV4, IPV6], [4, 6]):
                        if not IPV and event['event_type'] != BGPStream_Website_Event_Types.OUTAGE.value:
                            sql = f"""SELECT COUNT({t.prefix_column})
                                      FROM {t.name}
                                      WHERE family({t.prefix_column}) = {num}"""
                            assert t.get_count(sql) == 0
 
    def test_parse_common_elements(self, setup):
        """Tests the parse_common_elements function

        Should have input for every combo of:
            -hijack, leak, outage
            -country info vs non country info
        And check expected output.
        """
        for event in setup.events:
            data = Test_Data.init(event)
            with patch('lib_bgp_data.utils.utils.get_tags') as mock:
                mock.side_effect = setup.open_custom_HTML
                as_info, extended_children = data._parse_common_elements(event['row'])
               
                assert event['as_info'] == as_info
                assert event['extended_children'] == extended_children

    def test_parse_as_info(self, setup):
        """Tests the parse_as_info function

        Should have input for every combo of:
            -hijack, leak, outage
            -country info vs non country info
            -every possible combo if as info formatting
        And check expected output.
        """
        for event in setup.events:
            d = Test_Data.init(event)

            as_info = event['as_info']
                
            # the AS info for outages will be a a single string
            if isinstance(as_info, str):
                assert event['parsed_as_info1'] == d._parse_as_info(as_info)

            # for hijacks and leaks, there are 2 pieces of AS info in a list
            elif isinstance(as_info, list):
                assert event['parsed_as_info1'] == d._parse_as_info(as_info[1])
                assert event['parsed_as_info2'] == d._parse_as_info(as_info[3])


    def test_format_temp_row(self, setup):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """
        # test by putting the same string for every column except ID
        # what should returned is just the a list of the same string
        # the string that's put for ID should not be found
        for event in setup.events:
            data = Test_Data.init(event)
            # usually initialized in append
            data._temp_row = {}

            for col in data._columns:
                # id columns is ignored
                if col == 'id':
                    data._temp_row[col] = 'should not be here'
                # quotes should be removed
                else:
                    data._temp_row[col] = 'no quotes"'

            expected = ['no quotes' for i in range(len(data._columns)-1)]
            assert data._format_temp_row() == expected

    def test_parse_uncommon_info(self, setup):
        """Tests the parse_uncommon_elements function

        input all kinds of rows and check expected output.
        """
        for event in setup.events:
            data = Test_Data.init(event)

            # initialize temp row. it's usually initialized in append()
            data._temp_row = {}
            data._parse_uncommon_info(event['as_info'], event['extended_children'])
            for info in Test_Data.uncommon_info(event):
                assert data._temp_row[info] == event[info]


