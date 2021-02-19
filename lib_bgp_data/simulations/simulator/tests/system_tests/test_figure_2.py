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



class Test_Figure_2(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_figure_2a(self):
        r"""v1 example with ROV

               44\ \
              /|  \ \
             / |   \ 666
            /  | 88 \
          77   | /\  \
          /    78  86 \
        11     |     \ \
               12     99
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROV]
        peer_rows = []
        provider_customer_rows = [[44, 666],
                                  [44, 77],
                                  [44, 78],
                                  [44, 99],
                                  [77, 11],
                                  [78, 12],
                                  [88, 78],
                                  [88, 86],
                                  [86, 99]]
        # Set adopting rows
        bgp_ases = [11, 44, 12, 88, 86, 99, 666]
        adopting_ases = [77, 78]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, 0])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROV.value, 1])

        attacker = 666
        victim = 99

        exr_output = [{"asn": 44,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 11,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 77},
                      {"asn": 77,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 44},
                      {"asn": 12,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 44,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 44,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99}]

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

    def test_figure_2b(self):
        r"""v1 example with ROV++v1

               44\ \
              /|  \ \
             / |   \ 666
            /  | 88 \
          77   | /\  \
          /    78  86 \
        11     |     \ \
               12     99
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V1]
        peer_rows = []
        provider_customer_rows = [[44, 666],
                                  [44, 77],
                                  [44, 78],
                                  [44, 99],
                                  [77, 11],
                                  [78, 12],
                                  [88, 78],
                                  [88, 86],
                                  [86, 99]]
        # Set adopting rows
        bgp_ases = [11, 44, 12, 88, 86, 99, 666]
        adopting_ases = [77, 78]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, 0])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V1.value, 1])

        attacker = 666
        victim = 99

        #exr_output = [{"asn": 7,
        #               "prefix": Attack.default_prefix,
        #               "origin": 7,
        #               "received_from_asn": Conds.NOTHIJACKED.value},
        #              {"asn": 3,
        #               "prefix": Attack.default_prefix,
        #               "origin": 7,
        #               "received_from_asn": 6},

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)
