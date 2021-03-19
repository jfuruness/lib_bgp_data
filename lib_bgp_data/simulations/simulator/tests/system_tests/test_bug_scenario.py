#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""


import pytest

from .graph_tester import Graph_Tester
#from ..tables import Hijack
from ....enums import Non_Default_Policies, Policies, Data_Plane_Conditions as Conds
from ...attacks.attack_classes import Prefix_Superprefix_Hijack
from ...attacks.attack import Attack


__author__ = "Reynaldo Morillo"
__credits__ = ["Reynaldo Morillo"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"



class Test_Bug_Scenario(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_bug_scenario_v1(self):
        r"""

	TODO: create a png of scenario and keep in this directory.
        Link to scenario depiction (last slide)
        https://docs.google.com/presentation/d/14N7Jifs5ExPKrdWTabSjjbG8QW6R8us91bJpK8ZkRXk/edit?usp=sharing
        """

        attack_types = [Prefix_Superprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V1]
        peer_rows = [[2914, 1299],
		     [24875, 52320],
		     [52320, 12389]]
        provider_customer_rows = [[174, 213371],
                                  [174, 31133],
                                  [213371, 208673],
                                  [31133, 1299],
                                  [1299, 12389],
                                  [2914, 24875],
                                  [24875, 213371],
                                  [52320, 53180],
                                  [53180, 268337],
                                  [268337, 269494],
				  [12389, 33892]]
        # Set adopting rows
        bgp_ases = [174, 31133, 2914, 52320, 1299, 12389, 33892]
        rov_adopting_ases = []
        rovpp_adopting_ases = [213371, 208673, 24875, 53180, 268337, 269494]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in rov_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROV.value, True])
        for adopting_as in rovpp_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V1.value, True])

        attacker = 33892
        victim = 269494

        exr_output = [{"asn": 269494,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": Conds.NOTHIJACKED.value},
		      {"asn": 269494,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 268337},
                      {"asn": 268337,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": 269494},
		      {"asn": 268337,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 53180},
		      {"asn": 53180,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": 268337},
		      {"asn": 53180,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 52320},
		      {"asn": 52320,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": 53180},
		      {"asn": 52320,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 12389},
		      {"asn": 24875,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": 52320},
		      {"asn": 24875,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 2914},
		      {"asn": 213371,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": 24875},
		      {"asn": 213371,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 24875},
		      {"asn": 208673,
                       "prefix": Attack.default_prefix,
                       "origin": 269494,
                       "received_from_asn": 213371},
		      {"asn": 208673,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 213371},
		      {"asn": 174,
                       "prefix": Attack.default_prefix,
                       "origin": 33892,
                       "received_from_asn": 31133},
		      {"asn": 174,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 31133},
		      {"asn": 31133,
                       "prefix": Attack.default_prefix,
                       "origin": 33892,
                       "received_from_asn": 1299},
		      {"asn": 31133,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 1299},
		      {"asn": 1299,
                       "prefix": Attack.default_prefix,
                       "origin": 33892,
                       "received_from_asn": 12389},
		      {"asn": 1299,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 12389},
		      {"asn": 2914,
                       "prefix": Attack.default_prefix,
                       "origin": 33892,
                       "received_from_asn": 1299},
		      {"asn": 2914,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 1299},
		      {"asn": 12389,
                       "prefix": Attack.default_prefix,
                       "origin": 33892,
                       "received_from_asn": 33892},
		      {"asn": 12389,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
                       "received_from_asn": 33892},
                      {"asn": 33892,
                       "prefix": Attack.default_prefix,
                       "origin": 33892,
                       "received_from_asn": Conds.HIJACKED.value},
		      {"asn": 33892,
                       "prefix": Attack.default_superprefix,
                       "origin": 33892,
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

