#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the bgpstream_website_parser.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness", "Tony Zheng"]
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from unittest.mock import Mock, patch
from itertools import chain, combinations
from ..bgpstream_website_parser import utils, BGPStream_Website_Parser
from ..tables import Hijacks_Table, Leaks_Table, Outages_Table
from ..data_classes import Hijack, Leak, Outage
from ..event_types import BGPStream_Website_Event_Types
from ....utils import utils
from ....utils.database import Database, Generic_Table
from bs4 import BeautifulSoup as Soup
from time import strftime, gmtime, time
import re

########################
### Helper Functions ###
########################

def generate_event_combos():
    """Returns all possible combinations of Hijacks, Leaks, and Outages"""
    # https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset
    events = BGPStream_Website_Event_Types.list_values()
    return chain.from_iterable(combinations(events, r)
                               for r in range(len(events) + 1))

def generate_params():
    """Generates all combinations of parameters parser can be ran with.
       Used for parametrizing test_run."""
    params = []

    # custom HTML or run normally, pulling from bgpstream.com
    for custom in [False, True]:
        # all combinations of Hijacks, Leaks, Outages
        for combination in generate_event_combos():
            # No row limit, a fitting row limit, or too high row limit
            for row_limit in [None, 5, 999999]:
                # Only IPV4, only IPV6, or both, or neither
                for IPV4, IPV6 in combinations([True, False], 2):
                    params.append((custom, row_limit, IPV4, IPV6, combination))
    return params

def type_table_list():
    """Convenient for associating the the data type to its table"""
    for _type, table in zip(BGPStream_Website_Event_Types.list_values(),
                           [Hijacks_Table, Leaks_Table, Outages_Table]):
        yield _type, table

def row_count():
    """Returns the number of rows across all 3 tables"""
    count = 0
    for _type, table in type_table_list():
        with table() as t:
            count += t.get_count()
    return count

@pytest.mark.bgpstream_website_parser
class Test_BGPStream_Website_Parser:
    """Tests all local functions within the BGPStream_Website_Parser class."""

    @pytest.fixture
    def parser(self):
        return BGPStream_Website_Parser()

    @pytest.mark.slow(reason="Runs the parser many times. Will take hours.")
    @pytest.mark.parametrize('custom, row_limit, IPV4, IPV6, combination', generate_params())
    def test_run(self, parser, custom, row_limit, IPV4, IPV6, combination, setup):
        """Tests _run function

        Should use every possible combination of parameters with your own
        hidden html file and the website. When working with the hidden html
        file, assert that output is exactly what you expect. With the website
        assert that the output is approximately what you expect (for instance,
        more than 0 hijacks, shouldn't have empty fields, etc.
        """
        # beginning every test with empty tables
        for _type, table in type_table_list():
            with table(clear=True) as t:
                pass

        if custom:
            with patch('lib_bgp_data.utils.utils.get_tags') as mock:
                mock.side_effect = setup.open_custom_HTML
                parser._run(row_limit, IPV4, IPV6, combination)
        else:
            parser._run(row_limit, IPV4, IPV6, combination)

        if row_limit:
            assert row_count() <= row_limit

        for _type, table in type_table_list():
            for IPV, num in zip([IPV4, IPV6], [4, 6]):
                with table() as t:
                    # checks unselected IPV are not in tables
                    if not IPV and _type != BGPStream_Website_Event_Types.OUTAGE.value:
                       sql = f'SELECT COUNT({t.prefix_column}) FROM {t.name}\
                                WHERE family({t.prefix_column}) = {num}'
                       assert t.get_count(sql) == 0

                    # check unselected data types are not in tables
                    if _type not in combination:
                        assert t.get_count() == 0

                    print(t.get_count())
            
    @pytest.mark.parametrize('row_limit', [None, 5, 999999])
    @pytest.mark.parametrize('custom', [True, False])
    def test_get_rows(self, parser, row_limit, custom, setup):
        """Tests get rows func

        For real website, hidden file in this dir:
            -gets proper amount of rows
            -subtracts 10 rows if no limit
            -If limit is too high or none, results in rows - 10
            -if limit is lower, make sure it returns proper amount
        NOTE: try using mock to insert your own html. If that doesn't work,
        add a keyword arg to the get rows func.
        """
        if custom:
            with patch('lib_bgp_data.utils.utils.get_tags') as mock:
                mock.side_effect = setup.open_custom_HTML
                rows = utils.get_tags('https://bgpstream.com', 'tr')
                num_parsed_rows = len(parser._get_rows(row_limit))
        else:
            rows = utils.get_tags('https://bgpstream.com', 'tr')
            num_parsed_rows = len(parser._get_rows(row_limit))

        # if no row limit or row limit is too high, should be total - 10
        if row_limit is None or row_limit > len(rows):
            assert num_parsed_rows == len(rows) - 10
        # otherwise, it should be the row limit
        else:
            assert num_parsed_rows == row_limit

    def test_get_row_front_page_info(self, parser, setup):
        """Tests the get_row_front_page_info function

        Should insert three different dummy rows and make sure
        that all of them return the desired output. Should also
        try a row with and without contry/flag.
        Prob should parametize this function.
        """
        for event in setup.events:
            _type, start, end, url, event_num = \
            parser._get_row_front_page_info(event['row'])

            # there are subtle differences between how
            # bgpstream_website_parser and data_classes parses this info.
            # For constistency sake, search for returned text in HTML

            # you can omit the 'find_all' method call
            # tag(*args) is equivalent to tag.find_all(*args)
            assert len(event['row'](string=re.compile(_type))) != 0
            # slicing removes the '+00:00' that is added in the function
            assert len(event['row'](string=re.compile(start[:-6]))) != 0
            if end != 'None':
                assert len(event['row'](string=re.compile(end[:-6]))) != 0

            assert len(event['row'](href=re.compile(url))) != 0
            assert len(event['row'](href=re.compile(event_num))) != 0

    def test_generate_known_events(self, parser):
        """Tests the generate_known_events function

        Fill hijack, leak, and outage table with dummy info
        Get the dictionary back and make sure all rows are in the dict
        Make sure it doesn't fail if one of the tables is empty either.
        Parametize is prob required.
        """
        # insert rows with this info
        test_event_number = 1
        test_start_time = strftime('%Y-%m-%d %H:%M:%S', gmtime(time() - 86400)) + '+00:00'
        test_end_time = strftime('%Y-%m-%d %H:%M:%S', gmtime(time())) + '+00:00'

        for _type, table in type_table_list():
            with table(clear=True) as t:
                # insert an event into each table
                t.execute(f"""INSERT INTO {t.name}
                              (event_number, start_time, end_time)
                              VALUES(%s, %s::timestamp with time zone,
                                         %s::timestamp with time zone)""",
                          [test_event_number, test_start_time, test_end_time])

                # event_numbers need to be distinct because dict keys
                test_event_number += 1

        # check that event was properly generated
        events = parser._generate_known_events()
        for event_number in range(1, 4):
            assert events[event_number] == (test_start_time, test_end_time)




