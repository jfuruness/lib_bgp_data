#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_parser.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

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
 
    @pytest.mark.skip(reason="New hires work")
    def test_format_temp_row(self):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """

        pass

@pytest.mark.bgpstream_website_parser
class Test_Leak:
    """Tests all functions within the Leak class."""

    @pytest.mark.skip(reason="New hires work")
    def test_parse_uncommon_elements(self):
        """Tests the parse_uncommon_elements function

        input all kinds of Leak rows and check expected output.
        """

        pass
 
    @pytest.mark.skip(reason="New hires work")
    def test_format_temp_row(self):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """

        pass

@pytest.mark.bgpstream_website_parser
class Test_Outage:
    """Tests all functions within the Outage class."""

    @pytest.mark.skip(reason="New hires work")
    def test_parse_uncommon_elements(self):
        """Tests the parse_uncommon_elements function

        input all kinds of Outage rows and check expected output.
        """

        pass
 
    @pytest.mark.skip(reason="New hires work")
    def test_format_temp_row(self):
        """Tests the format temp row func function

        Make sure list exists with all columns but ID.
        """

        pass

