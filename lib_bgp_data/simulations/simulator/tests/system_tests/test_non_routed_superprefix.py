#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""


import pytest

from .graph_tester import Graph_Tester
#from ..tables import Hijack
from ....enums import Non_Default_Policies, Policies, Data_Plane_Conditions as Conds
from ...attacks.attack_classes import Unannounced_Prefix_Superprefix_Hijack
from ...attacks.attack import Attack


__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"



class Test_Non_Routed_Superprefix(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_non_routed_superprefix_rov(self):
        r"""non_routed superprefix attack with v1

              44
            /   \
           77    666
          /      
         11      

         superprefix = 1.0.0.0/8
         non_routed_prefix = 1.2.0.0/16

         TODO: Finish, test is not complete
        """

        attack_types = [Unannounced_Prefix_Superprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROV]
        peer_rows = []
        provider_customer_rows = [[44, 77],
                                  [44, 666],
                                  [77, 11]]
        # Set adopting rows
        bgp_ases = [44, 11, 666]
        adopting_ases = [77]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
             adopting_rows.append([adopting_as, Policies.ROV.value, True])

        attacker = 666
        victim = 99

        exr_output = [
                 {'asn': 11, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 77},
                 {'asn': 44, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 666},
                 {'asn': 44, 'origin': 666, 'prefix': '1.2.0.0/16', 'received_from_asn': 666},
                 {'asn': 77, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 44},
                 {'asn': 666, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 64513},
                 {'asn': 666, 'origin': 666, 'prefix': '1.2.0.0/16', 'received_from_asn': 64513}
                ]

        traceback_dict = {11:Conds.HIJACKED,
                          44:Conds.HIJACKED,
                          77:Conds.HIJACKED,
                          666:Conds.HIJACKED}

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output,
                         traceback_dict=traceback_dict)

    @pytest.mark.parametrize("adopt_pol",
                             [Non_Default_Policies.ROVPP_V1,
                              Non_Default_Policies.ROVPP_V2_AGGRESSIVE,
                              Non_Default_Policies.ROVPP_V2]) 
    def test_non_routed_superprefix_rovpp(self, adopt_pol):
        r"""non_routed superprefix attack with v1

              44
            /   \
           77    666
          /      
         11      

         superprefix = 1.0.0.0/8
         non_routed_prefix = 1.2.0.0/16

         TODO: Finish, test is not complete
        """

        attack_types = [Unannounced_Prefix_Superprefix_Hijack]
        adopt_policies = [adopt_pol]
        peer_rows = []
        provider_customer_rows = [[44, 77],
                                  [44, 666],
                                  [77, 11]]
        # Set adopting rows
        bgp_ases = [44, 11, 666]
        adopting_ases = [77]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
             adopting_rows.append([adopting_as, adopt_pol.value, True])

        attacker = 666
        victim = 99

        #exr_output = [
        #         {'asn': 11, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 77},
        #         {'asn': 44, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 666},
        #         {'asn': 44, 'origin': 666, 'prefix': '1.2.0.0/16', 'received_from_asn': 666},
        #         {'asn': 77, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 44},
        #         {'asn': 77, 'prefix': '1.2.0.0/16', 'origin': 64512, 'received_from_asn': 64512},
        #         {'asn': 666, 'origin': 666, 'prefix': '1.0.0.0/8', 'received_from_asn': 64513},
        #         {'asn': 666, 'origin': 666, 'prefix': '1.2.0.0/16', 'received_from_asn': 64513}
        #        ]
        exr_output = None 

        traceback_dict = {11:Conds.BHOLED,
                          44:Conds.HIJACKED,
                          77:Conds.BHOLED,
                          666:Conds.HIJACKED}

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output,
                         traceback_dict=traceback_dict)


