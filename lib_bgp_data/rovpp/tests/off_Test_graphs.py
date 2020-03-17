#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""

from .graph_tester import Graph_Tester
from ..tables import Hijack
from ..enums import Hijack_Types, Conditions as Conds

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"



class Test_Graphs(Graph_Tester):
    """Tests all example graphs within our paper."""

    def test_ex(self):
        """For a more in depth explanation, see _test_example"""
        
        # Figure 1a from SIGCOMM paper
        hijack = Hijack({"attacker": 666,
                         "more_specific_prefix": "1.2.3.0/24",
                         "victim": 99,
                         "expected_prefix": "1.2.0.0/16"})
        hijack_type = Hijack_Types.SUBPREFIX_HIJACK.value
        peers = []
        # NOTE PROVIDERS IS FIRST!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # [PROVIDER | CUSTOMER
        customer_providers = [[44, 77],
                              [44, 78],
                              [44, 666],
                              [44, 99],
                              [88, 78],
                              [88, 86],
                              [77, 11],
                              [78, 12],
                              [86, 99]]
        # populates rovpp ases
        # ASN | policy_num | impliment (impliment is true if policy_num != 0, but doesn't matter here
        as_list = [[44, 0, 0],
                   [88, 0, 0],
                   [77, 1, 1],
                   [666, 0, 0],
                   [11, 0, 0],
                   [78, 1, 1],
                   [12, 0, 0],
                   [86, 0, 0],
                   [99, 0, 0]]
       
        #  [ asn   |   prefix   | origin | received_from_asn | time | alternate_as | opt_flag ]
        output = [[11, "1.2.0.0/16", 99, 77, 1, 0, None],
                  [12, "1.2.0.0/16", 99, 78, 1, 0, None],
                  [44, "1.2.0.0/16", 99, 99, 1, 0, None],
                  [44, "1.2.3.0/24", 666, 666, 1, 0, None],
                  [77, "1.2.0.0/16", 99, 44, 1, 0, None],
                  [78, "1.2.0.0/16", 99, 44, 1, 0, None],
                  [86, "1.2.0.0/16", 99, 99, 1, 0, None],
                  [88, "1.2.0.0/16", 99, 86, 1, 0, None],
                  [99, "1.2.0.0/16", 99, Conds.NOTHIJACKED.value, 1, 0, None],
                  [99, "1.2.3.0/24", 666, Conds.NOTHIJACKED.value, 1, 0, None],  # MUST BE REMOVED
                  [666, "1.2.0.0/16", 99, 44, 1, 0, None],
                  [666, "1.2.3.0/24", 666, Conds.HIJACKED.value, 1, 0, None]]

        # How is this called test called?
        self._graph_example(hijack, hijack_type, peers, customer_providers, as_list, output)
