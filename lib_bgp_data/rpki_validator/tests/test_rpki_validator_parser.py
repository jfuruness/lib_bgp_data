#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the rpki_validator_parser.py file.
For specifics on each test, see docstrings under each function.
"""

import pytest
from ..rpki_validator_parser import RPKI_Validator_Parser
from ...utils import utils


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

@pytest.mark.rpki_validator
class Test_RPKI_Validator_Parser:
    """Tests all local functions within the RPKI_Validator_Parser class."""

    @pytest.mark.skip(reason="New hires will work on this")
    def test_parser_test_data(self):
        """This is more of an overall system test,

        since most all of the functionality exists in the wrapper.
        This test will input a few prefix origins we know are invalid
        (which we can tell using the roas collector) and a few we know
        are valid into a test table. Then we can confirm that the output
        is what we expect.
        """

        pass

    @pytest.mark.skip(reason="new hire will work on this")
    def test__format_asn_dict(self):
        """Tests the format asn_dict function

        Confirms that the output is what we expect for a typical entry"""

        pass

    @pytest.mark.skip(reason="new hire will work on this")
    @pytest.mark.slow
    def test_comprehensive_system(self):
        """Tests the entire system on the MRT announcements.

        Assert that there are no mrt announcments missing.
        NOTE: It's possible RPKI Validator removes duplicates
        of prefix origin pairs. Check for this.

        IN ADDITION: You should check that after you get data
        initially, that if you wait longer you do not get more
        data. In the past, we've had problems where the data
        had not loaded in time. I think we figured out the fix,
        but def need to test here. Don't want to test in a
        different func because this unit test will take hours.
        """

        pass
