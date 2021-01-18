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
            RPKI_Validator_Parser()._run(table=test_table)
            sql_val = f'SELECT validity FROM rov_validity WHERE origin = 0'
            sql_inval = f'SELECT validity FROM rov_validity WHERE origin = 1'

            assert db.execute(sql_val)[0]['validity'] == 1
            assert db.execute(sql_inval)[0]['validity'] == -2

    def test__format_asn_dict(self, parser):
        """Tests the format asn_dict function

        Confirms that the output is what we expect for a typical entry"""
        for key, value in RPKI_Validator_Wrapper.get_validity_dict().items():
            d = {'asn': 'AS198051', 'prefix': '1.2.0.0/16', 'validity': key}
            assert parser._format_asn_dict(d) == [198051, '1.2.0.0/16', value]

    @pytest.mark.slow
    def test_comprehensive_system(self):
        """Tests the entire system on the MRT announcements.

        Assert that there are no mrt announcments missing.
        # The API returns incomplete data. The following 
        # origins paired with a prefix of 0.0.0.0/0
        # don't show up:
        # 2914, 3257, 3356, 6830, 9002, 30781, 33891
        NOTE: It's possible RPKI Validator removes duplicates
        of prefix origin pairs. Check for this.

        IN ADDITION: You should check that after you get data
        initially, that if you wait longer you do not get more
        data. In the past, we've had problems where the data
        had not loaded in time. I think we figured out the fix,
        but def need to test here. Don't want to test in a
        different func because this unit test will take hours.
        """

        missing_origins = {2914, 3257, 3356, 6830, 9002, 30781, 33891}

        with ROV_Validity_Table() as db:

            # Run MRT_Parser to fill mrt_announcements table which will
            # be used as the input table for RPKI_Validator.
            # Use only one collector and remove isolario to make it faster.
            input_table = MRT_Announcements_Table.name
            mods = {'collectors[]': ['route-views2', 'rrc03']}
            no_isolario = [MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS]
            MRT_Parser().run(api_param_mods=mods, sources=no_isolario)
            
            RPKI_Validator_Parser().run(table=input_table)

            initial_count = db.get_count()

            for row in db.execute(f'SELECT prefix, origin FROM {input_table}'):
                prefix, origin = row['prefix'], row['origin']

                sql = (f"SELECT COUNT(*) FROM {db.name} WHERE "
                       f"prefix = '{prefix}' AND origin = {origin}")

                count = db.get_count(sql)

                api_miss = (count == 0
                            and prefix == '0.0.0.0/0'
                            and origin in missing_origins)

                # There should be exactly one of this prefix-origin pair
                # or it's data that's missing from the API.
                assert count == 1 or api_miss

            # There should be no new data straggling behind. 
            sleep(120)
            assert initial_count == db.get_count()
