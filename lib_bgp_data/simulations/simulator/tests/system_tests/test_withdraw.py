#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator pertaining to withdrawls.

For speciifics on each test, see the docstrings under each function.
"""

import pytest

from .graph_tester import Graph_Tester
#from ..tables import Hijack
from ....enums import Non_Default_Policies, Policies, Data_Plane_Conditions as Conds
from ...attacks.attack_classes import Subprefix_Hijack, Prefix_Hijack
from ...attacks.attack import Attack


__author__ = "Cameron Morris"
__credits__ = ["Cameron Morris"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_Withdraw(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_simple_withdraw(self):
        r"""Simple test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 

        exr_output = [{"asn": 1,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": 3},
                      {"asn": 2,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": 1},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 5,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 7},
                      {"asn": 7,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": Conds.NOTHIJACKED.value}]
        self._withdraw_check(Non_Default_Policies.ROV, exr_output)

    def test_rovpp_v1_withdraw(self):
        r"""Simple 0.1 test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """

        exr_output = [{"asn": 1,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": 3},
                      {"asn": 2,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": 1},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 4,
                       "prefix": Attack.default_prefix,
                       "origin": Conds.BHOLED.value,
                       "received_from_asn": Conds.BHOLED.value},
                      {"asn": 5,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 7},
                      {"asn": 7,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": Conds.NOTHIJACKED.value}]
        self._withdraw_check(Non_Default_Policies.ROVPP_V1, exr_output)

    @pytest.mark.parametrize("adopt_pol",
                             [Non_Default_Policies.ROVPP_V2_AGGRESSIVE,
                              Non_Default_Policies.ROVPP_V2,
                              Non_Default_Policies.ROVPP_V3])
    def test_rovpp_v23_withdraw(self, adopt_pol):
        r"""Simple 0.2 test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 
        exr_output = [{"asn": 1,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": 3},
                      {"asn": 2,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": 1},
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 3,
                       "received_from_asn": Conds.HIJACKED.value},
                      {"asn": 4,
                       "prefix": Attack.default_prefix,
                       "origin": Conds.BHOLED.value,
                       "received_from_asn": Conds.BHOLED.value},
                      {"asn": 5,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": 7},
                      {"asn": 6,
                       "prefix": Attack.default_prefix,
                       "origin": Conds.BHOLED.value,
                       "received_from_asn": 4},
                      {"asn": 7,
                       "prefix": Attack.default_prefix,
                       "origin": 7,
                       "received_from_asn": Conds.NOTHIJACKED.value}]
        self._withdraw_check(adopt_pol, exr_output)

    def test_rovpp_v3_withdraw2(self):
        r"""0.3 test case for withdrawals.
           This time, not identical to 0.2 for this case.

                   1
                  / \
                 3   2 
                    /|\  
                   4 5 6
        """ 

        attack_types = [Subprefix_Hijack]
        adopt_policies = [Non_Default_Policies.ROVPP_V3]
        peer_rows = []
        provider_customer_rows = [[1, 3],
                                  [1, 2],
                                  [2, 4],
                                  [2, 5],
                                  [2, 6]] 

        bgp_ases = [1, 3, 4, 5, 6, 7]
        adopting_ases = [2]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as,
                                  Non_Default_Policies.ROVPP_V3.value,
                                  True])

        attacker = 3
        victim = 6

        # Here, we should see preventive announcements at 2, 4 and 5.  We should
        # *not* see a preventive announcement at 6.
        exr_output = [{"asn": 1,
                       "prefix": Attack.default_prefix,
                       "origin": 6,
                       "received_from_asn": 2}, 
                      {"asn": 1,
                       "prefix": Attack.default_subprefix,
                       "origin": 3,
                       "received_from_asn": 3},
                      {"asn": 2,
                       "prefix": Attack.default_prefix,
                       "origin": 6,
                       "received_from_asn": 6}, 
                      {"asn": 2,
                       "prefix": Attack.default_subprefix,
                       "origin": 6,
                       "received_from_asn": 6},
                      {"asn": 3,
                       "prefix": Attack.default_subprefix,
                       "origin": 3,
                       "received_from_asn": Conds.HIJACKED.value}, 
                      {"asn": 3,
                       "prefix": Attack.default_prefix,
                       "origin": 6,
                       "received_from_asn": 1},
                      {"asn": 4,
                       "prefix": Attack.default_prefix,
                       "origin": 6,
                       "received_from_asn": 2}, 
                      {"asn": 4,
                       "prefix": Attack.default_subprefix,
                       "origin": 6,
                       "received_from_asn": 2},
                      {"asn": 5,
                       "prefix": Attack.default_prefix,
                       "origin": 6,
                       "received_from_asn": 2}, 
                      {"asn": 5,
                       "prefix": Attack.default_subprefix,
                       "origin": 6,
                       "received_from_asn": 2},
                      {"asn": 6,
                       "prefix": Attack.default_prefix,
                       "origin": 6,
                       "received_from_asn": Conds.NOTHIJACKED.value}]

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)

####################
### Helper Funcs ###
####################

    def _withdraw_check(self, adopt_pol, exr_output):
        r"""Simple test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 

        attack_types = [Prefix_Hijack]
        adopt_policies = [adopt_pol]
        peer_rows = [[1,2]]
        provider_customer_rows = [[1, 3],
                                  [1, 4],
                                  [1, 5],
                                  [4, 6],
                                  [5, 7]] 

        # One problem with double-propagation is  that since the victim
        # propagates first, the victim's announcement will get withdrawn. In
        # the past, this would be done by overwriting the old announcement, but
        # if 4 adopts, then 6 will not get the overwritten announcement.
        # Withdrawals solve this.

        bgp_ases = [1, 2, 3, 5, 6, 7]
        adopting_ases = [4]
        adopting_rows = []
        for bgp_as in bgp_ases:
            adopting_rows.append([bgp_as, Policies.DEFAULT.value, False])
        for adopting_as in adopting_ases:
            adopting_rows.append([adopting_as, adopt_pol.value, True])

        attacker = 3
        victim = 7

        self._test_graph(attack_types=attack_types,
                         adopt_policies=adopt_policies,
                         peer_rows=peer_rows,
                         provider_customer_rows=provider_customer_rows,
                         adopting_rows=adopting_rows,
                         attacker=attacker,
                         victim=victim,
                         exr_output=exr_output)
