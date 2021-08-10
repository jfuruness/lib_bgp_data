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



class Test_Figure_1(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_figure_1a(self):
        r"""hidden hijack example with bgp

          44
            \
            88 - 77
            /     \
           99      666
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.BGP]
        peer_rows = [[88, 77]]
        provider_customer_rows = [[44, 88],
                                  [88, 99],
                                  [77, 666]]
        # Set adopting rows
        bgp_ases = [44, 88, 77, 99, 666]
        adopting_ases = []
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        # for adopting_as in adopting_ases:
        #     adopting_rows.append([adopting_as, Policies.ROVPP_V3.value, 1])

        attacker = 666
        victim = 99

        exr_output = [{"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 88},
                      {"asn": 88,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 77,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 88},
                      {"asn": 99,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                      {"asn": 666,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 77},
                      {"asn": 88,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 77},
                      {"asn": 77,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 666},
                      {"asn": 99,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                      {"asn": 666,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                     ]

        results_dict = {"trace_hijacked_collateral": 3,
                        "trace_nothijacked_collateral": 0,
                        "trace_blackholed_collateral": 0,
                        "trace_total_collateral": 3,
                        "trace_hijacked_adopting": 0,
                        "trace_nothijacked_adopting": 0,
                        "trace_blackholed_adopting": 0,
                        "trace_total_adopting": 0}

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output,
                         results_dict=results_dict)

    def test_figure_1b(self):
        r"""hidden hijack example with ROV

          44
            \
            78
             \
             88
             / \
            99 666
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROV]
        peer_rows = []
        provider_customer_rows = [[44, 78],
                                  [78, 88],
                                  [88, 99],
                                  [88, 666]]
        # Set adopting rows
        bgp_ases = [44, 88, 99, 666]
        adopting_ases = [78]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROV.value, True])

        attacker = 666
        victim = 99

        exr_output = [{"asn": 44,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 78},
                      {"asn": 88,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 99},
                      {"asn": 78,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 88},
                      {"asn": 99,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                      {"asn": 666,
                       "prefix": Attack.default_prefix,
                       "origin": 99,
                       "received_from_asn": 88},
                      {"asn": 88,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": 666},
                      {"asn": 99,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.NOTHIJACKED.value},
                      {"asn": 666,
                       "prefix": Attack.default_subprefix,
                       "origin": 666,
                       "received_from_asn": Conds.HIJACKED.value},
                     ]


        results_dict = {"trace_hijacked_collateral": 2,
                        "trace_nothijacked_collateral": 0,
                        "trace_blackholed_collateral": 0,
                        "trace_total_collateral": 2,
                        "trace_hijacked_adopting": 1,
                        "trace_nothijacked_adopting": 0,
                        "trace_blackholed_adopting": 0,
                        "trace_total_adopting": 1}


        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output,
                         results_dict=results_dict)
