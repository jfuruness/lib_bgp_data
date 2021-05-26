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


__author__ = "Reynaldo Morillo"
__credits__ = ["Reynaldo Morillo"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"



class Test_Special_Cases(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_v2_customer_blackhole(self):
        r"""
             55
           /    \
         44      3
                /  \
              666   77

        Here we're testing that v2 ASes should not create blackhole announcements for attack
        announcements received from a customer, but rather just drop and blackhole the announcement.
        That can be capture here as 55 and 44 implementing ASes. AS 44 should not have a blackhole, but
        AS 55 should have a blackhole.
        """

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V2]
        peer_rows = []
        provider_customer_rows = [[55, 44],
                                  [55, 3],
                                  [3, 666],
                                  [3, 77]]
        # Set adopting rows
        bgp_ases = [3, 666, 77]
        rov_adopting_ases = []
        rovpp_adopting_ases = [55, 44]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
#        for adopting_as in rov_adopting_ases:
#            adopting_rows.append([adopting_as, Policies.ROV.value, True])
        for adopting_as in rovpp_adopting_ases:
            adopting_rows.append([adopting_as, Policies.ROVPP_V2.value, True])

        attacker = 666
        victim = 77

        exr_output = [
				 {'asn': 77, 'origin': 77, 'prefix': '1.2.0.0/16', 'received_from_asn': 64514},
				 {'asn': 77, 'origin': 666, 'prefix': '1.2.3.0/24', 'received_from_asn': 64514},
				 {'asn': 44, 'origin': 77, 'prefix': '1.2.0.0/16', 'received_from_asn': 55},
				 {'asn': 55, 'origin': 77, 'prefix': '1.2.0.0/16', 'received_from_asn': 3},
				 {'asn': 55,
				  'origin': 64512,
				  'prefix': '1.2.3.0/24',
				  'received_from_asn': 64512},
				 {'asn': 3, 'origin': 77, 'prefix': '1.2.0.0/16', 'received_from_asn': 77},
				 {'asn': 3, 'origin': 666, 'prefix': '1.2.3.0/24', 'received_from_asn': 666},
				 {'asn': 666, 'origin': 77, 'prefix': '1.2.0.0/16', 'received_from_asn': 3},
				 {'asn': 666,
				  'origin': 666,
				  'prefix': '1.2.3.0/24',
				  'received_from_asn': 64513}
		     ]

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

