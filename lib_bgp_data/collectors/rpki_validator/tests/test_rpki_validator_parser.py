#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the rpki_validator_parser.py file.
For specifics on each test, see docstrings under each function.
"""

from time import sleep

import pytest

from ..rpki_validator_parser import RPKI_Validator_Parser
from ..rpki_validator_wrapper import RPKI_Validator_Wrapper
from ..tables import ROV_Validity_Table
from ...mrt.mrt_base import MRT_Parser, MRT_Sources
from ...mrt.mrt_base.tables import MRT_Announcements_Table
from ....utils import utils
from ....utils.base_classes import ROA_Validity as Val


__authors__ = ["Justin Furuness, Tony Zheng"]
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

@pytest.mark.rpki_validator
class Test_RPKI_Validator_Parser:
    """Tests all local functions within the RPKI_Validator_Parser class."""

    @pytest.fixture
    def parser(self):
        return RPKI_Validator_Parser()

    def test_parser_test_data(self, test_table):
        """This is more of an overall system test,

        since most all of the functionality exists in the wrapper.
        This test will input a few prefix origins we know are invalid
        (which we can tell using the roas collector) and a few we know
        are valid into a test table. Then we can confirm that the output
        is what we expect.
        """
        
        with ROV_Validity_Table() as db:

            def _get_val_for_origin(origin):
                sql = f"""SELECT validity FROM {db.name}
                          WHERE origin = {origin};"""
                return db.execute(sql)[0]['validity']

            # see conftest.py in this dir for test_table details
            RPKI_Validator_Parser()._run(table=test_table)

            # sometimes unknown validity status is returned by the API
            # and it doesn't get the correct one unless waited on
            valid = _get_val_for_origin(0)
            assert valid == Val.VALID.value or valid == Val.UNKNOWN.value

            invalid = _get_val_for_origin(1)
            assert invalid == Val.INVALID_BY_ORIGIN.value or invalid == Val.UNKNOWN.value

    def test__format_asn_dict(self, parser):
        """Tests the format asn_dict function

        Confirms that the output is what we expect for a typical entry"""
        for key, value in RPKI_Validator_Wrapper.get_validity_dict().items():
            d = {'asn': 'AS198051', 'prefix': '1.2.0.0/16', 'validity': key}
            assert parser._format_asn_dict(d) == [198051, '1.2.0.0/16', value]

    @pytest.mark.xfail(strict=True)
    @pytest.mark.slow
    def test_comprehensive_system(self):
        """Tests the entire system on the MRT announcements.

        Test is expected to fail. RPKI Validator does not
        have data on all prefix-origin pairs.

        RPKI Validator also changes validity values if waited. 
        """

        with ROV_Validity_Table() as db:

            # Run MRT_Parser to fill mrt_announcements table which will
            # be used as the input table for RPKI_Validator.
            input_table = MRT_Announcements_Table.name
            MRT_Parser().run()

            RPKI_Validator_Parser().run(table=input_table)

            initial_count = db.get_count()
            initial_rows = db.get_all()
 
            # all prefix-origin pairs from input should be in val table
            sql = f"""SELECT * FROM {input_table} a
                      LEFT JOIN {db.name} b
                      USING (prefix, origin)
                      WHERE b.prefix IS NULL;"""
            assert len(db.execute(sql)) == 0

            # clear validity table and run with a wait before getting data
            # should be the same with and without waiting
            db.clear_table()

            RPKI_Validator_Parser().run(table=input_table, wait=True)

            second_count = db.get_count()
            second_rows = db.get_all()

            assert initial_count == second_count
            assert initial_rows == second_rows
