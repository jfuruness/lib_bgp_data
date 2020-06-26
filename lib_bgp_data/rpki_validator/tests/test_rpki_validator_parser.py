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
from ...mrt_parser.mrt_parser import MRT_Parser
from ...utils import utils


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
            print(db.execute(f'SELECT * FROM {test_table}'))
            assert False
            

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
        NOTE: It's possible RPKI Validator removes duplicates
        of prefix origin pairs. Check for this.

        IN ADDITION: You should check that after you get data
        initially, that if you wait longer you do not get more
        data. In the past, we've had problems where the data
        had not loaded in time. I think we figured out the fix,
        but def need to test here. Don't want to test in a
        different func because this unit test will take hours.
        """
        with ROV_Validity_Table() as db:
            MRT_Parser()._run()
                
            print('TABLES')
            for i in db.execute("SELECT * FROM information_schema.tables WHERE table_schema='public'"):
                print(i['table_name'])
            RPKI_Validator_Parser(table_input='mrt_announcements')._run()
            print('RPKI_Validator finished')
            print('TABLES')
            for i in db.execute("SELECT * FROM information_schema.tables WHERE table_schema='public'"):
                print(i['table_name'])
            """            
            try:
                #db.execute('CREATE SCHEMA IF NOT EXISTS public')
                MRT_Parser()._run()
                print('MRT Parser finished')
                # rpki_validator_parser doesn't accept kwargs so rename table to the default

                #db.execute('ALTER TABLE test.mrt_announcements RENAME TO mrt_rpki')


            except Exception as e:
                print(e)
            """
            """
            except Exception as e:
                print(e)
                print('SCHEMAS:')
                for i in db.execute('SELECT schema_name FROM information_schema.schemata'):
                    print(i['schema_name'])


            print('TABLES')
            for i in db.execute("SELECT * FROM information_schema.tables WHERE table_schema='public'"):
                print(i['table_name'])
                        
            sql = 'SELECT COUNT(*) FROM rov_validity'
            initial_count = db.get_count(sql)

            print('initial count: ', initial_count)

            # no mrt announcements missing
            for pair in db.execute('SELECT * FROM mrt_announcements'):
                prefix = pair['prefix']
                origin = pair['origin']
                count =  db.get_count('SELECT * FROM mrt_announcements WHERE'
                                   f'prefix = {prefix} AND origin = {origin}')
                # asserts for existance and removal of dupes
                assert count == 1

            print('Finished checking for single existence')

            # no new data
            sleep(120)
            final_count = db.get_count(sql)
            assert initial_count == final_count
            print('test finished')
            """
