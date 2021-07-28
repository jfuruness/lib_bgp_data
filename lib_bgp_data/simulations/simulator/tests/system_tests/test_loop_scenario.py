#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""


import pytest

from .graph_tester import Graph_Tester
#from ..tables import Hijack
from ....enums import Non_Default_Policies, Policies, Data_Plane_Conditions as Conds
from ...attacks.attack_classes import Subprefix_Hijack
from ...attacks.attack import Attack


__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"



class Test_Loop_Scenario(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_loop_scenario_v3(self):
        r"""v3 loop scenario
        TODO Create topology image
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V3]
        peer_rows = [[666, 1],
                     [666, 4]]
        provider_customer_rows = [[1, 2],
                                  [1, 5],
                                  [2, 3],
                                  [4, 3],
                                  [4, 5],
                                  [3, 6],
                                  [5, 6],
                                  [6, 7]]
        # Set adopting rows
        bgp_ases = [666]
        adopting_ases = [1, 2, 3, 4, 5, 6, 7]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V3.value, True])

        attacker = 666
        victim = 7

        exr_output = [{"asn": 7,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                     {"asn": 6,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 7},
                     {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                     {"asn": 5,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
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
                     {"asn": 1,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 5},
                      {"asn": 1,
                       "prefix": Attack.default_subprefix,
                       "origin": 7,
                       "received_from_asn": 5},
                      {"asn": 666,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 4},
                      {"asn": 666,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},

		     ]

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

