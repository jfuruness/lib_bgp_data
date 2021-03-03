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



class Test_Figure_4(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_figure_4a(self):
        r"""v3 example with ROV++v2

              /44\
            53 |  666
           /   |   \ 
          /    | 87 \ 
         54    |/  \ \
          \    33   99
           \  /       
            22
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V2]
        peer_rows = []
        provider_customer_rows = [[44, 53],
                                  [44, 33],
                                  [44, 99],
                                  [44, 666],
                                  [53, 54],
                                  [54, 22],
                                  [33, 22],
                                  [87, 33],
                                  [87, 99]]
        # Set adopting rows
        bgp_ases = [54, 53, 22, 44, 87, 99, 666]
        adopting_ases = [33]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V2.value, True])

        attacker = 666
        victim = 99

        exr_output = [{"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 44,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 666},
                      {"asn": 666,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 44},
                      {"asn": 666,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 53,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 44},
                      {"asn": 53,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 44},
                      {"asn": 54,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 53},
                      {"asn": 54,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 53},
                      {"asn": 22,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 33},
                      {"asn": 22,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 54},
                      {"asn": 87,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 33,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 87},
                      {"asn": 99,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": Conds.NOTHIJACKED.value },
                      {"asn": 99,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.NOTHIJACKED.value},
		     ]

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

    def test_figure_4b(self):
        r"""v3 example with ROV++v2

              /44\
            53 |  666
           /   |   \ 
          /    | 87 \ 
         54    |/  \ \
          \    33   99
           \  /       
            22
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V3]
        peer_rows = []
        provider_customer_rows = [[44, 53],
                                  [44, 33],
                                  [44, 99],
                                  [44, 666],
                                  [53, 54],
                                  [54, 22],
                                  [33, 22],
                                  [87, 33],
                                  [87, 99]]
        # Set adopting rows
        bgp_ases = [54, 53, 22, 44, 87, 99, 666]
        adopting_ases = [33]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V3.value, True])

        attacker = 666
        victim = 99

        exr_output = [{"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 44,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 666},
                      {"asn": 666,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 44},
                      {"asn": 666,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 53,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 44},
                      {"asn": 53,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 44},
                      {"asn": 54,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 53},
                      {"asn": 54,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 53},
                      {"asn": 22,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 33},
                      {"asn": 22,
                       "prefix": Attack.default_subprefix,
                       "origin": 99,
                       "received_from_asn": 33},
                      {"asn": 87,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 33,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 87},
                      {"asn": 33,
                       "prefix": Attack.default_subprefix,
                       "origin": 99,
                       "received_from_asn": 87},
                      {"asn": 99,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": Conds.NOTHIJACKED.value },
                      {"asn": 99,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.NOTHIJACKED.value},
		     ]



        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)
