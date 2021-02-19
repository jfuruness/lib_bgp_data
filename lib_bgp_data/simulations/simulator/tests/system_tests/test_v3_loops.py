#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator pertaining to withdrawls.

For speciifics on each test, see the docstrings under each function.
"""

import pytest

from .graph_tester import Graph_Tester
#from ..tables import Hijack
from ....enums import Non_Default_Policies, Policies, Data_Plane_Conditions as Conds
from ...attacks.attack_classes import Subprefix_Hijack
from ...attacks.attack import Attack


__author__ = "Cameron Morris, Justin Furuness"
__credits__ = ["Cameron Morris, Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Test_V3_Loops(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_rovpp_v3_loops(self):
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

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V3]
        peer_rows = []
        provider_customer_rows = [[44, 77],
                                  [44, 78],
                                  [44, 99],
                                  [44, 666],
                                  [77, 11],
                                  [78, 12],
                                  [88, 78],
                                  [88, 86],
                                  [86, 99]]
        # Set adopting rows
        bgp_ases = [44, 11, 12, 88, 86, 99, 666]
        adopting_ases = [77, 78]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, 0])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V3.value, 1])
       
        attacker = 666
        victim = 99
      
        assert False, "Must run this later" 
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        exr_output = [{"asn": 7,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_subprefix,
                       "origin": 7,
                       "received_from_asn": 2},
                      {"asn": 5,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 5,
                       "prefix": Attack.default_subprefix,
                       "origin": 7,
                       "received_from_asn": 4},
                      {"asn": 1,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 5},
                      {"asn": 1,
                       "prefix": Attack.default_subprefix,
                       "origin": 7,
                       "received_from_asn": 5},
                      {"asn": 6,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 7},
                      {"asn": 666,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 1},
                      {"asn": 666,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 4,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 5},
                      {"asn": 4,
                       "prefix": Attack.default_subprefix,
                       "origin": 7,
                       "received_from_asn": 3},
                      {"asn": 2,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 3},
                      {"asn": 2,
                       "prefix": Attack.default_subprefix,
                       "origin": 7,
                       "received_from_asn": 1},
                    ]

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

if __name__ == "__main__":
   Test_V3_Loops().test_rovppbp_loops3()
