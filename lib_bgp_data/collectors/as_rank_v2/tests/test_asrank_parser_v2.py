#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the as_rank_v2_parser.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Nicholas Shpetner"]
__credits__ = ["Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

from ..as_rank_v2_parser import AS_Rank_Parser_V2
from ..tables import AS_Rank_V2

@pytest.mark.asrank_parser_v2
class Test_AS_Rank_Parser_V2:

    def test_quick_run(self):
        """Checks the first 10 ranked ASNs and makes sure everything
        is formatted properly and inserted"""
        parser = AS_Rank_Parser_V2()
        parser._run(0, 10)
        with AS_Rank_V2() as db:
            result = db.execute('SELECT count(*) FROM as_rank_v2')
            assert result[0]['count'] == 10
            first_row = db.execute('SELECT * FROM as_rank_v2 LIMIT 1')
            first_row = first_row[0]
            links = first_row['links']
            org = first_row['organization']
            rank = first_row['rank']
            assert links is not None
            for link in links:
                assert type(link) == int
            assert type(org) == str
            assert rank == 1

    @pytest.mark.slow
    def test_full(self):
        """This does not verify formatting, quick_run does that. This
        instead makes sure that the parser pulls all ASNs from Caida.
        Also this is INCREDIBLY SLOW, takes 6-ish hours to complete"""
        parser = AS_Rank_Parser_V2()
        count = parser._run() - 1
        with AS_Rank_V2() as db:
            result = db.execute('SELECT count(*) FROM as_rank_v2')
            assert result[0]['count'] == count

