#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""

from ..rovpp_simulator import ROVPP_Simulator
from ..tables import Hijack, Subprefix_Hijack_Table
from ...utils import Database, db_connection, utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_Graphs:
    """Tests all example graphs within our paper."""

    def test_ex_1(self):
        """For a more in depth explanation, see _test_example"""

        1/0

########################
### Helper Functions ###
########################

    def _test_example(self, hijack, peers, customer_providers, as_list, output):
        """tests example graphs from paper

        Input:
            hijack: hijack class, with ann info
            peers: list of Peers, rows in peers table
            customer_providers: list of Customer_Provier pairs, rows in customer_providers table
            as_list: list of ases and what they are implimenting
            output: list of rows in exr output (classes)

        Craetes attackers/victims, peers, customer_providers, and rovpp_test_ases. Runs exr. Verifies output."""

        1/0
        # NOTE: call relatinoship_parser, just insert your own csvs!!! or maybe mock func of csv_creation?
        # NOTE: this then creates all relationship tables and rovpp_ases. Then just update rovpp_ases table
        # NOTE: after that, call I think subprefix hijac table, which creats attackers and victims
        # NOTE: then call exr, maybe using the normal exr call?
        # NOTE: verify the output against another table? Create this table myself?
