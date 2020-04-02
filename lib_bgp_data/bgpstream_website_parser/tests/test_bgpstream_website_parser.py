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
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..tables import Hijacks_Table, Leaks_Table, Outages_Table
from ..data_classes import Hijack, Leak, Outage
from ..event_types import Event_Types
from ...utils import utils
from ...database import Database
from bs4 import BeautifulSoup as Soup
from time import strftime, gmtime, time
from .open_custom_HTML import open_custom_HTML

def generate_event_combos():
    """Returns possible combinations of events to be parsed"""
    # https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset
    events = Event_Types.list_values()
    return chain.from_iterable(combinations(events, r) for r in range(len(events) + 1))

def generate_params(custom: bool):
    """Generator for all possible parameter combinations.
       If testing on custom HTML, a more appropriate row_limit is used."""
    limits = [None, 3, 999999] if custom else [None, 100, 999999]

    for combination in generate_event_combos():
        for row_limit in [None, 100, 999999]:
            for IPV in combinations([True, False], 2):
                yield (row_limit, *IPV, combination)

def table_list():
    for table in [Hijacks_Table(), Leaks_Table(), Outages_Table()]:
        yield table

def fresh_tables():
    """Recreates tables so that they have no data in them"""
    with Database() as _db:
        for table in table_list():
            name = table.name
            _db.execute(f'DROP TABLE IF EXISTS {name}')
            table._create_tables()

def row_count():
    with Database() as _db:
        return _db.execute("""SELECT(SELECT COUNT(*) FROM hijacks) +
                                    (SELECT COUNT(*) FROM leaks) +
                                    (SELECT COUNT(*) FROM outages) AS count""")[0]['count']


def IPV_check(IPV: bool, event_type: str):
    """Returns True if there exists rows with IPV in event_type table."""
    # setting the table name and prefix column for sql query
    if event_type == Event_Types.HIJACK.value:
        name = Hijacks_Table().name
        prefix = Hijacks_Table().prefix_column
    elif event_type == Event_Types.LEAK.value:
        name = Leaks_Table().name
        prefix = Leaks_Table().prefix_column

    with Database() as _db:
        count = 0
        try:
            count +=  _db.execute(f'SELECT COUNT({prefix}) FROM {name} WHERE family({prefix}) = {IPV}')[0]['count']
        except:
            return False
        return count > 0

@pytest.mark.bgpstream_website_parser
class Test_BGPStream_Website_Parser:
    """Tests all local functions within the BGPStream_Website_Parser class."""

    @pytest.mark.slow(reason="Needs to query website many times")
    def test_run(self):
        """Tests _run function

        Should use every possible combination of parameters with your own
        hidden html file and the website. When working with the hidden html
        file, assert that output is exactly what you expect. With the website
        assert that the output is approximately what you expect (for instance,
        more than 0 hijacks, shouldn't have empty fields, etc.
        """

        parser = BGPStream_Website_Parser()

        for params in generate_params(False):
            # recreates tables as empty
            fresh_tables()
            parser._run(*params)

            row_count = row_count()

            row_limit = params[0]
            IPV4 = 4 if params[1] else False
            IPV6 = 6 if params[2] else False
            data_types = params[3]

            # if a row limit was set, the number of events parsed should be less than or equal to limit
            if row_limit:
                assert row_count <= row_limit

            for IPV in [IPV4, IPV6]:
                for event in data_types:
                    # Hijacks can have IPV4 and IPV6, so if either are selected for parsing, IPV_check should return True
                    if IPV and event == Event_Types.HIJACK.value:
                        assert IPV_check(IPV, event)
                    # Leaks only have IPV4
                    elif IPV == 4 and event == Event_Types.LEAK.value:
                        assert IPV_check(IPV, event)
                    # Otherwise, the IPV is not selected for parsing, it's a combination of Leaks and IPV6,
                    # Or outages that have no prefixes
                    else:
                        assert not IPV_check(IPV, event)


    @patch('lib_bgp_data.utils.utils.get_tags', autospec=True)
    def test_run_custom(self, mock_get_tags):
        mock_get_tags.side_effect = open_custom_HTML

        parser = BGPStream_Website_Parser()

        for params in generate_params(True):
            fresh_tables()
            parser._run(*params)

            row_limit = params[0]
            IPV4 = params[1]
            IPV6 = params[2]
            data_types = params[3]

            if row_limit == 3:
                assert row_count() == 3
            else:
                required_count = 0
                # there are 2 hijacks, 1 leak, and 4 outages in the custom HTML
                for event, count in zip(Event_Types.list_values(), [2, 1, 4]):
                    if event in data_types:
                        required_count += count
                assert required_count == row_count()

                # if all rows are parsed, also check for IPV filtering
                with Database() as _db:
                    sql = 'SELECT * FROM {} WHERE event_number = {}'

                    # if IPV4 is parsed, check that these events, which have IPV4 prefixes, are in the tables
                    if IPV4:
                        if Event_Types.HIJACK.value in data_types:
                            assert len(_db.execute(sql.format(Hijacks_Table().name, 229087))) == 1
                        if Event_Types.LEAK.value in data_types:
                            assert len(_db.execute(sql.format(Leaks_Table().name, 229100))) == 1

                    # if IPV6 is parsed, check that this hijack was inserted
                    if IPV6:
                        if Event_Types.HIJACK.value in data_Types:
                            assert len(_db.execute(sql.format(Hijacks_Table().name, 230097))) == 1


    def test_get_rows(self):
        """Tests get rows func

        For real website, hidden file in this dir:
            -gets proper amount of rows
            -subtracts 10 rows if no limit
            -If limit is too high or none, results in rows - 10
            -if limit is lower, make sure it returns proper amount
        NOTE: try using mock to insert your own html. If that doesn't work,
        add a keyword arg to the get rows func.
        """
        parser = BGPStream_Website_Parser()

        # test row_limits and if the row_limit should be used
        row_limits = [(None, False), (20, True), (999999, False)]

        for l in row_limits:
            rows = utils.get_tags("https://bgpstream.com", "tr")
            if l[1]:
                assert len(parser._get_rows(l[0])) == l[0]
            else:
                assert len(parser._get_rows(l[0])) == len(rows) - 10

        # checks with custom HTML that has 1 hijack, 1 outage, and 1 leak
        with patch('lib_bgp_data.utils.utils.get_tags') as mock_get_tag:
            mock_get_tag.side_effect = open_custom_HTML
            assert len(parser._get_rows(None)) == 3
            assert len(parser._get_rows(2)) == 2
            assert len(parser._get_rows(999999)) == 3


    def test_get_row_front_page_info(self):
        """Tests the get_row_front_page_info function

        Should insert three different dummy rows and make sure
        that all of them return the desired output. Should also
        try a row with and without contry/flag.
        Prob should parametize this function.
        """
        tags = open_custom_HTML('./test_HTML/page.html', 'tr')[:3]

        parser = BGPStream_Website_Parser()
        outage_info = ('Outage', '2020-03-18 22:31:00+00:00', '2020-03-18 22:34:00+00:00', '/event/229106', '229106')
        leak_info = ('BGP Leak', '2020-03-18 20:26:10+00:00', 'None', '/event/229100', '229100')
        hijack_info = ('Possible Hijack', '2020-03-18 17:41:23+00:00', 'None', '/event/229087', '229087')
        infos = [outage_info, leak_info, hijack_info]

        for i in range(len(tags)):
            assert parser._get_row_front_page_info(tags[i]) == infos[i]

    def test_generate_known_events(self):
        """Tests the generate_known_events function

        Fill hijack, leak, and outage table with dummy info
        Get the dictionary back and make sure all rows are in the dict
        Make sure it doesn't fail if one of the tables is empty either.
        Parametize is prob required.
        """
        # inserts a dummy event into hijack, tests if generate_known_events gets dummy event, deletes dummy event
        test_event_number = 1
        test_start_time = strftime('%Y-%m-%d %H:%M:%S', gmtime(time() - 86400))
        test_end_time = strftime('%Y-%m-%d %H:%M:%S', gmtime(time()))

        for _Table_Class in [Hijacks_Table, Leaks_Table, Outages_Table]:
            with _Table_Class() as _db:
                _db.execute(f"""INSERT INTO {_db.name}(event_number, start_time, end_time)
                            VALUES(%s, %s::timestamp with time zone, %s::timestamp with time zone)""",
                            [test_event_number, test_start_time, test_end_time])
        events = BGPStream_Website_Parser()._generate_known_events()
        assert events[test_event_number] == (test_start_time + '+00:00', test_end_time + '+00:00')

        for _Table_Class in [Hijacks_Table, Leaks_Table, Outages_Table]:
            with _Table_Class() as _db:
                _db.execute(f"DELETE FROM {_db.name} WHERE event_number={test_event_number}")


