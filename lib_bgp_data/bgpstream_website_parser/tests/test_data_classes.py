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
from .open_custom_HTML import open_custom_HTML
from ..data_classes import Data, Hijack, Leak, Outage

@pytest.mark.bgpstream_website_parser
class Test_Data:
    """Tests all functions within the Data class.

    NOTE: You may want to make this not a test class
    and simply have all other classes inherit it."""

    @pytest.mark.skip(reason="New hires work")
    def test_append(self):
        """Tests the append function

        Should have input for every combo of:
            -hijack, leak, outage
            -country info vs non country info
        And check expected output.
        """

        pass
    @pytest.mark.skip(reason="New hires work")
    def test_db_insert(self):
        """Tests the db_insert function

        Should have input with the powerset of all the combinations of:
            -hijack, leak, outage
            -country info vs non country info
        And check expected output.
        """

        pass
    @pytest.mark.skip(reason="New hires work")
    def test_parse_common_elements(self):
        """Tests the parse_common_elements function

        Should have input for every combo of:
            -hijack, leak, outage
            -country info vs non country info
        And check expected output.
        """

        pass

    @pytest.mark.skip(reason="New hires work")
    def test_parse_as_info(self):
        """Tests the parse_as_info function

        Should have input for every combo of:
            -hijack, leak, outage
            -country info vs non country info
            -every possible combo if as info formatting
        And check expected output.
        """

        pass


@pytest.mark.bgpstream_website_parser
class Test_Hijack:
    """Tests all functions within the Hijack class."""

    @pytest.mark.skip(reason="New hires work")
    def test_parse_uncommon_elements(self):
        """Tests the parse_uncommon_elements function

        input all kinds of Hijack rows and check expected output.
        """

        pass
 
    def test_format_temp_row(self):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """

        hijack = Hijack('./')

        row = open_custom_HTML('./test_HTML/page.html', 'tr')[2]

        self._temp_row = []

        with patch('lib_bgp_data.utils.utils.get_tags') as mock_get_tag:
            mock_get_tag.side_effect = open_custom_HTML
            hijack._parse_uncommon_info(*hijack._parse_common_elements(row))

        #expected output
        return_list = ['', '{131477, 138576, 3257, 28329, 265888, 2}', '8', 'UDEL-DCN, US', '2', '2020-03-18 17:41:23',
                       '', '229087', 'Possible Hijack', 'BULL-HN, US', '6', '128.201.254.0/23', '128.201.254.0/23',
                       '/event/229087']
        assert hijack._format_temp_row() == return_list

@pytest.mark.bgpstream_website_parser
class Test_Leak:
    """Tests all functions within the Leak class."""

    @pytest.mark.skip(reason="New hires work")
    def test_parse_uncommon_elements(self):
        """Tests the parse_uncommon_elements function

        input all kinds of Leak rows and check expected output.
        """

        pass


    def test_format_temp_row(self):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """
        leak = Leak('./')

        row = open_custom_HTML('./test_HTML/page.html', 'tr')[1]

        self._temp_row = {}

        with patch('lib_bgp_data.utils.utils.get_tags') as mock_get_tag:
            mock_get_tag.side_effect = open_custom_HTML
            leak._parse_uncommon_info(*leak._parse_common_elements(row))

        #expected output
        return_list = ['', '12', '2020-03-18 20:26:10', '', '229100', 'BGP Leak',
                       '{28642, 267469, 267613, 3549, 3356, 3910, 209, 3561, 40685}', '162.10.252.0/24',
                       "{'LEVEL3, US'}", '{3356}', 'CENTURYLINK-EUROPE-LEGACY-QWEST, US', '3910', 'ANACOMP-SD, US',
                       '40685', '/event/229100']
        assert leak._format_temp_row() == return_list


@pytest.mark.bgpstream_website_parser
class Test_Outage:
    """Tests all functions within the Outage class."""

    @pytest.mark.skip(reason="New hires work")
    def test_parse_uncommon_elements(self):
        """Tests the parse_uncommon_elements function

        input all kinds of Outage rows and check expected output.
        """

        pass
 
    def test_format_temp_row(self):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """
        outage = Outage('./')

        row = open_custom_HTML('./test_HTML/page.html', 'tr')[0]

        self._temp_row = {}

        with patch('lib_bgp_data.utils.utils.get_tags') as mock_get_tag:
            mock_get_tag.side_effect = open_custom_HTML
            outage._parse_uncommon_info(*outage._parse_common_elements(row))

        #expected output
        return_list = [None, None, 'DO', '2020-03-18 22:31:00', '2020-03-18 22:34:00',
                       '229106', 'Outage', '167 ', '27', '/event/229106']

        assert outage._format_temp_row() == return_list



