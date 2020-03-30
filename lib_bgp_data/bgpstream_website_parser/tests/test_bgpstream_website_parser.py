
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
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..tables import Hijacks_Table, Leaks_Table, Outages_Table
from ..data_classes import Hijack, Leak, Outage
from ..event_types import Event_Types
from ...utils import utils
from ...database import Database
from bs4 import BeautifulSoup as Soup
from time import strftime, gmtime, time
from .open_custom_HTML import open_custom_HTML

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
        def drop():
            _db.execute('DROP TABLE IF EXISTS hijacks')
            _db.execute('DROP TABLE IF EXISTS leaks')
            _db.execute('DROP TABLE IF EXISTS outages')

        event_combos = [[Event_Types.HIJACK.value],
                        [Event_Types.LEAK.value],
                        [Event_Types.OUTAGE.value],
                        [Event_Types.HIJACK.value, Event_Types.LEAK.value],
                        [Event_Types.HIJACK.value, Event_Types.OUTAGE.value],
                        [Event_Types.LEAK.value, Event_Types.OUTAGE.value],
                        [Event_Types.HIJACK.value, Event_Types.LEAK.value, Event_Types.OUTAGE.value]]

        parser = BGPStream_Website_Parser()

        for combination in event_combos:
            for row_limit in [None, 100, 999999]:
                for IPV in [(False, False), (True, False), (False, True), (True, True)]:
                    with Database() as _db:
                        drop()
                        parser._run(row_limit, IPV[0], IPV[1], combination, False)

                        row_count = 0

                        if Event_Types.HIJACK.value in combination:
                            hijack_count = _db.execute('SELECT COUNT(*) FROM hijacks')[0]['count']
                            assert hijack_count > 0
                            row_count += hijack_count

                            if IPV[0]:
                                sql = 'SELECT expected_prefix FROM hijacks WHERE family(expected_prefix) = 4'
                                assert len(_db.execute(sql)) > 0
                            if IPV[1]:
                                sql = 'SELECT expected_prefix FROM hijacks WHERE family(expected_prefix) = 6'
                                assert len(_db.execute(sql)) > 0

                        if Event_Types.LEAK.value in combination:
                            leak_count = _db.execute('SELECT COUNT(*) FROM leaks')[0]['count']
                            assert leak_count > 0
                            row_count += leak_count

                            if IPV[0]:
                                sql = 'SELECT leaked_prefix FROM leaks WHERE family(leaked_prefix) = 4'
                                assert len(_db.execute(sql)) > 0

                        if Event_Types.OUTAGE.value in combination:
                            outage_count = _db.execute('SELECT COUNT(*) FROM outages')[0]['count']
                            assert outage_count > 0
                            row_count += outage_count

                        if row_limit == 100:
                            assert 0 < row_count <= 100

    @patch('lib_bgp_data.utils.utils.get_tags', autospec=True)
    def test_run_custom(self, mock_get_tags):
        mock_get_tags.side_effect = open_custom_HTML

        def drop():
            _db.execute('DROP TABLE IF EXISTS hijacks')
            _db.execute('DROP TABLE IF EXISTS leaks')
            _db.execute('DROP TABLE IF EXISTS outages')

        event_combos = [[Event_Types.HIJACK.value],
                        [Event_Types.LEAK.value],
                        [Event_Types.OUTAGE.value],
                        [Event_Types.HIJACK.value, Event_Types.LEAK.value],
                        [Event_Types.HIJACK.value, Event_Types.OUTAGE.value],
                        [Event_Types.LEAK.value, Event_Types.OUTAGE.value],
                        [Event_Types.HIJACK.value, Event_Types.LEAK.value, Event_Types.OUTAGE.value]]

        parser = BGPStream_Website_Parser()

        for combination in event_combos:
            for row_limit in [None, 3, 999999]:
                for IPV in [(False, False), (True, False), (False, True), (True, True)]:
                    with Database() as _db:
                        drop()
                        parser._run(row_limit, IPV[0], IPV[1], combination, False)

                        if Event_Types.HIJACK.value in combination:
                            sql = """SELECT 1 FROM hijacks WHERE
                                     country is NULL AND
                                     detected_as_path = '{131477, 138576, 3257, 28329, 265888, 2}' AND
                                     detected_by_bgpmon_peers = '8' AND
                                     detected_origin_name = 'UDEL-DCN, US' AND
                                     detected_origin_number = '2' AND
                                     start_time = '2020-03-18 17:41:23' AND
                                     end_time is NULL AND
                                     event_number = '229087' AND
                                     event_type = 'Possible Hijack' AND
                                     expected_origin_name = 'BULL-HN, US' AND
                                     expected_origin_number = '6' AND
                                     expected_prefix = '128.201.254.0/23' AND
                                     more_specific_prefix = '128.201.254.0/23' AND
                                     url = '/event/229087'"""

                            assert len(_db.execute(sql)) == 1

                        if Event_Types.LEAK.value in combination:
                            sql = """SELECT 1 FROM leaks WHERE
                                     country is NULL AND
                                     detected_by_bgpmon_peers = '12' AND
                                     start_time = '2020-03-18 20:26:10' AND
                                     end_time is NULL AND
                                     event_number = '229100' AND
                                     event_type = 'BGP Leak' AND
                                     example_as_path = '{28642, 267469, 267613, 3549, 3356, 3910, 209, 3561, 40685}' AND
                                     leaked_prefix = '162.10.252.0/24' AND
                                     leaked_to_name = %s::varchar (200) ARRAY AND
                                     leaked_to_number = '{3356}' AND
                                     leaker_as_name = 'CENTURYLINK-EUROPE-LEGACY-QWEST, US' AND
                                     leaker_as_number = '3910' AND
                                     origin_as_name = 'ANACOMP-SD, US' AND
                                     origin_as_number = '40685' AND
                                     url = '/event/229100'"""

                            assert len(_db.execute(sql, (["'LEVEL3", "US'"],))) == 1

                        if Event_Types.OUTAGE.value in combination:
                            sql = """SELECT 1 FROM outages WHERE
                                     as_name is NULL AND
                                     as_number is NULL AND
                                     country = 'DO' AND
                                     start_time = '2020-03-18 22:31:00' AND
                                     end_time = '2020-03-18 22:34:00' AND
                                     event_number = '229106' AND
                                     event_type = 'Outage' AND
                                     number_prefixes_affected = '167' AND
                                     percent_prefixes_affected = '27' AND
                                     url = '/event/229106'"""

                            assert len(_db.execute(sql)) == 1

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


