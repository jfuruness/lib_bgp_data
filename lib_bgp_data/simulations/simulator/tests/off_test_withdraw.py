#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator pertaining to withdrawls.

For speciifics on each test, see the docstrings under each function.
"""

from .graph_tester import Graph_Tester
from ..tables import Hijack
from ..enums import Hijack_Types, Conditions as Conds


__author__ = "Cameron Morris"
__credits__ = ["Cameron Morris"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_Withdraw(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_simple_withdraw(self):
        """Simple test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 
        hijack = Hijack({"attacker": 3,
                         "more_specific_prefix": "1.2.0.0/16",
                         "victim": 7,
                         "expected_prefix": "1.2.0.0/16"})

        # One problem with double-propagation is  that since the victim
        # propagates first, the victim's announcement will get withdrawn. In
        # the past, this would be done by overwriting the old announcement, but
        # if 4 adopts, then 6 will not get the overwritten announcement.
        # Withdrawals solve this.

        hijack_type = Hijack_Types.PREFIX_HIJACK.value
        peers = [[1, 2]]
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[1, 3],
                              [1, 4],
                              [1, 5],
                              [4, 6],
                              [5, 7]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[1, 0, 0],
                   [2, 0, 0],
                   [3, 0, 0],
                   [4, 1, 1],
                   [5, 0, 0],
                   [6, 0, 0],
                   [7, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[1, "1.2.0.0/16", 3, 3, 1, 0, None],
                  [2, "1.2.0.0/16", 3, 1, 1, 0, None],
                  [3, "1.2.0.0/16", 3, Conds.HIJACKED.value, 1, 0, None],
                  [5, "1.2.0.0/16", 7, 7, 1, 0, None],
                  [7, "1.2.0.0/16", 7, Conds.NOTHIJACKED.value, 1, 0, None]]

        # How is this called test called?
        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)

    def test_rovpp_withdraw(self):
        """Simple 0.1 test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 
        hijack = Hijack({"attacker": 3,
                         "more_specific_prefix": "1.2.0.0/16",
                         "victim": 7,
                         "expected_prefix": "1.2.0.0/16"})

        # One problem with double-propagation is  that since the victim
        # propagates first, the victim's announcement will get withdrawn. In
        # the past, this would be done by overwriting the old announcement, but
        # if 4 adopts, then 6 will not get the overwritten announcement.
        # Withdrawals solve this.

        hijack_type = Hijack_Types.PREFIX_HIJACK.value
        peers = [[1, 2]]
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[1, 3],
                              [1, 4],
                              [1, 5],
                              [4, 6],
                              [5, 7]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[1, 0, 0],
                   [2, 0, 0],
                   [3, 0, 0],
                   [4, 2, 1],
                   [5, 0, 0],
                   [6, 0, 0],
                   [7, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[1, "1.2.0.0/16", 3, 3, 1, 0, None],
                  [2, "1.2.0.0/16", 3, 1, 1, 0, None],
                  [3, "1.2.0.0/16", 3, Conds.HIJACKED.value, 1, 0, None],
                  [4, "1.2.0.0/16", Conds.BHOLED.value, Conds.BHOLED.value, 1, 0, None],
                  [5, "1.2.0.0/16", 7, 7, 1, 0, None],
                  [7, "1.2.0.0/16", 7, Conds.NOTHIJACKED.value, 1, 0, None]]

        # How is this called test called?
        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)

    def test_rovppb_withdraw(self):
        """Simple 0.2 test case for withdrawals.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 
        hijack = Hijack({"attacker": 3,
                         "more_specific_prefix": "1.2.0.0/16",
                         "victim": 7,
                         "expected_prefix": "1.2.0.0/16"})

        hijack_type = Hijack_Types.PREFIX_HIJACK.value
        peers = [[1, 2]]
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[1, 3],
                              [1, 4],
                              [1, 5],
                              [4, 6],
                              [5, 7]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[1, 0, 0],
                   [2, 0, 0],
                   [3, 0, 0],
                   [4, 3, 1],
                   [5, 0, 0],
                   [6, 0, 0],
                   [7, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[1, "1.2.0.0/16", 3, 3, 1, 0, None],
                  [2, "1.2.0.0/16", 3, 1, 1, 0, None],
                  [3, "1.2.0.0/16", 3, Conds.HIJACKED.value, 1, 0, None],
                  [4, "1.2.0.0/16", Conds.BHOLED.value, Conds.BHOLED.value, 1, 0, None],
                  [5, "1.2.0.0/16", 7, 7, 1, 0, None],
                  [6, "1.2.0.0/16", Conds.BHOLED.value, 4, 1, 0, None],
                  [7, "1.2.0.0/16", 7, Conds.NOTHIJACKED.value, 1, 0, None]]

        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)

    def test_rovppbis_withdraw(self):
        """Simple 0.2bis test case for withdrawals.
           This should be identical to 0.2 for this case.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 
        hijack = Hijack({"attacker": 3,
                         "more_specific_prefix": "1.2.0.0/16",
                         "victim": 7,
                         "expected_prefix": "1.2.0.0/16"})

        hijack_type = Hijack_Types.PREFIX_HIJACK.value
        peers = [[1, 2]]
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[1, 3],
                              [1, 4],
                              [1, 5],
                              [4, 6],
                              [5, 7]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[1, 0, 0],
                   [2, 0, 0],
                   [3, 0, 0],
                   [4, 5, 1],
                   [5, 0, 0],
                   [6, 0, 0],
                   [7, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[1, "1.2.0.0/16", 3, 3, 1, 0, None],
                  [2, "1.2.0.0/16", 3, 1, 1, 0, None],
                  [3, "1.2.0.0/16", 3, Conds.HIJACKED.value, 1, 0, None],
                  [4, "1.2.0.0/16", Conds.BHOLED.value, Conds.BHOLED.value, 1, 0, None],
                  [5, "1.2.0.0/16", 7, 7, 1, 0, None],
                  [6, "1.2.0.0/16", Conds.BHOLED.value, 4, 1, 0, None],
                  [7, "1.2.0.0/16", 7, Conds.NOTHIJACKED.value, 1, 0, None]]

        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)

    def test_rovppbp_withdraw(self):
        """Simple 0.3 test case for withdrawals.
           This is also identical to 0.2 for this case.

                   1--2
                  /|\
                 3 4 5 
                   |  \
                   6   7
        """ 
        hijack = Hijack({"attacker": 3,
                         "more_specific_prefix": "1.2.0.0/16",
                         "victim": 7,
                         "expected_prefix": "1.2.0.0/16"})

        hijack_type = Hijack_Types.PREFIX_HIJACK.value
        peers = [[1, 2]]
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[1, 3],
                              [1, 4],
                              [1, 5],
                              [4, 6],
                              [5, 7]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[1, 0, 0],
                   [2, 0, 0],
                   [3, 0, 0],
                   [4, 4, 1],
                   [5, 0, 0],
                   [6, 0, 0],
                   [7, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[1, "1.2.0.0/16", 3, 3, 1, 0, None],
                  [2, "1.2.0.0/16", 3, 1, 1, 0, None],
                  [3, "1.2.0.0/16", 3, Conds.HIJACKED.value, 1, 0, None],
                  [4, "1.2.0.0/16", Conds.BHOLED.value, Conds.BHOLED.value, 1, 0, None],
                  [5, "1.2.0.0/16", 7, 7, 1, 0, None],
                  [6, "1.2.0.0/16", Conds.BHOLED.value, 4, 1, 0, None],
                  [7, "1.2.0.0/16", 7, Conds.NOTHIJACKED.value, 1, 0, None]]

        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)

    def test_rovppbp_withdraw2(self):
        """0.3 test case for withdrawals.
           This time, not identical to 0.2 for this case.

                   1
                  / \
                 3   2 
                    /|\  
                   4 5 6
        """ 
        hijack = Hijack({"attacker": 3,
                         "more_specific_prefix": "1.2.3.0/24",
                         "victim": 6,
                         "expected_prefix": "1.2.0.0/16"})

        # Here, we should see preventive announcements at 2, 4 and 5.  We should
        # *not* see a preventive announcement at 6.

        hijack_type = Hijack_Types.SUBPREFIX_HIJACK.value
        peers = []
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[1, 2],
                              [1, 3],
                              [2, 4],
                              [2, 5],
                              [2, 6]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[1, 0, 0],
                   [2, 4, 1],
                   [3, 0, 0],
                   [4, 0, 0],
                   [5, 0, 0],
                   [6, 0, 0],
                   [7, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[1, "1.2.0.0/16", 6, 2, 1, 0, None],
                  [1, "1.2.3.0/24", 3, 3, 1, 0, None],
                  [2, "1.2.0.0/16", 6, 6, 1, 0, None],
                  [2, "1.2.3.0/24", 6, 6, 1, 6, None],
                  [3, "1.2.3.0/24", 3, Conds.HIJACKED.value, 1, 0, None],
                  [3, "1.2.0.0/16", 6, 1, 1, 0, None],
                  [4, "1.2.0.0/16", 6, 2, 1, 0, None],
                  [4, "1.2.3.0/24", 6, 2, 1, 6, None],
                  [5, "1.2.0.0/16", 6, 2, 1, 0, None],
                  [5, "1.2.3.0/24", 6, 2, 1, 6, None],
                  [6, "1.2.0.0/16", 6, Conds.NOTHIJACKED.value, 1, 0, None]]

        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)
