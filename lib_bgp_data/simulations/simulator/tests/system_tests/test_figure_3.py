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



class Test_Figure_3(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_figure_3a(self):
        r"""v2 example with ROV++V1 and ROV

              /44\
             / / \\666
            /  54 \ 
           /  /    56
          77  55    \
           | /       99
          11    
          / \
         32 33  
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP]
        peer_rows = []
        provider_customer_rows = [[44, 77],
                                  [44, 54],
                                  [44, 56],
                                  [44, 666],
                                  [77, 11],
                                  [11, 32],
                                  [11, 33],
                                  [54, 55],
                                  [55, 11],
                                  [56, 99]]
        # Set adopting rows
        bgp_ases = [11, 54, 55, 44, 666, 56, 99]
        rov_adopting_ases = [32, 33]
        rovpp_adopting_ases = [77]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, 0])
        for adopting_as in rov_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROV.value, 1])
        for adopting_as in rovpp_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP.value, 1])

        attacker = 666
        victim = 99

        exr_output = [{"asn": 32,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                      {"asn": 33,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 6},

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

    def test_figure_3b(self):
        r"""v2 example with ROV++V1 and ROV

              /44\
             / / \\666
            /  54 \ 
           /  /    56
          77  55    \
           | /       99
          11    
          / \
         32 33  
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP]
        peer_rows = []
        provider_customer_rows = [[44, 77],
                                  [44, 54],
                                  [44, 56],
                                  [44, 666],
                                  [77, 11],
                                  [11, 32],
                                  [11, 33],
                                  [54, 55],
                                  [55, 11],
                                  [56, 99]]
        # Set adopting rows
        bgp_ases = [11, 54, 55, 44, 666, 56, 99]
        rov_adopting_ases = [32]
        rovpp_v2_adopting_ases = [77, 33]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, 0])
        for adopting_as in rov_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROV.value, 1])
        for adopting_as in rovpp_v2_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V2.value, 1])

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
