#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator pertaining to withdrawls.

For speciifics on each test, see the docstrings under each function.
"""

import pytest

from .graph_tester import Graph_Tester
from ..tables import Hijack
from ..enums import Hijack_Types, Conditions as Conds


__author__ = "Cameron Morris, Justin Furuness"
__credits__ = ["Cameron Morris, Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_V3_Loops(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_rovppbp_loops3(self):
        """Simple 0.3 test case for withdrawals.
           This is also identical to 0.2 for this case.

                    44 
                  / / \ \
                77 |   \  666 
                /  |    \
               /   |  88 \
              /    | /  \ \ 
             /     78    \ \
            /     /      86 \
           /     |         \ \
           |     |           v
          11     12          99
        """ 
        hijack = Hijack({"attacker": 666,
                         "more_specific_prefix": "1.2.3.0/24",
                         "victim": 99,
                         "expected_prefix": "1.2.0.0/16"})

        hijack_type = Hijack_Types.SUBPREFIX_HIJACK.value
        peers = []
        #peers = [[1,666]]
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[44, 77],
                              [44, 78],
                              [44, 99],
                              [44, 666],
                              [77, 11],
                              [78, 12],
                              [88, 78],
                              [88, 86],
                              [86, 99]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[44, 0, 0],
                   [77, 8, 1],
                   [11, 0, 0],
                   [78, 8, 1],
                   [12, 0, 0],
                   [88, 0, 0],
                   [86, 0, 0],
                   [99, 0, 0],
                   [666, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[7, "1.2.0.0/16", 7, Conds.NOTHIJACKED.value, 1, 0, None],
                  [3, "1.2.0.0/16", 7, 6, 1, 0, None],
                  [3, "1.2.3.0/24", 7, 2, 1, 5, None],
                  [5, "1.2.0.0/16", 7, 6, 1, 0, None],
                  [5, "1.2.3.0/24", 7, 4, 1, 3, None],
                  [1, "1.2.0.0/16", 7, 5, 1, 0, None],
                  [1, "1.2.3.0/24", 7, 5, 1, 5, None],
                  [6, "1.2.0.0/16", 7, 7, 1, 0, None],
                  [666, "1.2.0.0/16", 7, 1, 1, 0, None],
                  [666, "1.2.3.0/24", 666, Conds.HIJACKED.value, 1, 0, None],
                  [4, "1.2.0.0/16", 7, 5, 1, 0, None],
                  [4, "1.2.3.0/24", 7, 3, 1, 3, None],
                  [2, "1.2.0.0/16", 7, 3, 1, 0, None],
                  [2, "1.2.3.0/24", 7, 1, 1, 5, None]]

        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)
