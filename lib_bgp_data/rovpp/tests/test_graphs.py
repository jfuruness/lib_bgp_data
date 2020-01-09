#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""

from ..relationships_parser import Relationships_Parser
from ..rovpp_simulator import ROVPP_Simulator
from ...enums import Hijack_Types
from ..tables import Hijack, Subprefix_Hijack_Table
from ...utils import Database, db_connection, utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Hijack:
    def __init__(self, info_dict):
        self.attacker_asn = info_dict.get("attacker")
        self.attacker_prefix = info_dict.get("more_specific_prefix")
        self.victim_asn = info_dict.get("victim")
        self.victim_prefix = info_dict.get("expected_prefix")

class Test_Graphs:
    """Tests all example graphs within our paper."""

    def test_double_propogation(self):
        # double prop stored in rovpp_exrtrapolation_results
        exr_bash=("rovpp-extrapolator -v 1 "
                  "-t rovpp_top_100_ases "
                  "-t rovpp_etc_ases "
                  "-t rovpp_edge_ases "
                  "-b 0 "  # deterministic
                  "-k 1")  # double propogation
        ROVPP_Simulator().run(trials=1, percents=[30])
        exr_bash = exr_bash[:-1] + "0 -r exr_single_prop_test"
        Extrapolator().run_rovpp(exr_bash=exr_bash)
        with db_connection(
        

    def AAAAAtest_ex(self):
        """For a more in depth explanation, see _test_example"""

        hijack = Hijack({"attacker": 123,
                         "more_specific_prefix": "1.2.3.0/24",
                         "victim": 1,
                         "expected_prefix": "1.2.0.0/16"})
        hijack_type = Hijack_Types.SUBPREFIX_HIJACK.value
        peers = [[1, 2]
                 [2, 3]]

########################
### Helper Functions ###
########################

    def _graph_example(self, hijack, hijack_type, peers, customer_providers, as_list, output):
        """tests example graphs from paper

        Input:
            hijack: hijack class, with ann info
                contains attributes for 
            peers: list of Peers, rows in peers table
            customer_providers: list of [provider, customer] pairs, rows in customer_providers table
            as_list: list of ases and what they are implimenting
            output: list of rows in exr output (classes)

        Craetes attackers/victims, peers, customer_providers, and rovpp_test_ases. Runs exr. Verifies output."""

        # purely for inheritance
        class ROVPP_Extrapolation_Results_Test_Table(ROVPP_Extrapolation_Results_Table):
            pass

        # This first section creates all these tables from lists of lists
        # specifically, peers, customer providers, ases, and the extrapolator output
        utils.set_common_init_args()
        csvs = ["peers", "customer_providers", "ases", "exr_output"]
        rows = [peers, customer_providers, as_list, output]
        tables = [ROVPP_Peers_Table, ROVPP_Customer_Providers_Table, ROVPP_ASes_Table, ROVPP_Extrapolation_Results_Test_Table]

        csv_path = "/tmp/rovpp_tests/"
        utils.clean_paths(self.logger, csv_path)
        for csv, rows, table in zip(csvs, rows, tables):
            utils.rows_to_db(self.logger,
                             rows,
                             "{}{}.csv".format(csv_path, csv),
                             table,
                             clear_table=True)
        # Then creates subprefix hijac table, which creates attackers and victims
        with db_connection(self.logger, ROVPP_MRT_Announcements_Table) as db:
            db.populate_mrt_announcements(hijack, hijack_type)
        # Runs rov++ with our custom table names
        Extrapolator().run_rovpp(table_names=["rovpp_ases"])
        with db_connection() as db:
            sql = """SELECT * FROM rovpp_extrapolation_results_test
                  EXCEPT
                  SELECT * FROM rovpp_extrapolation_results"""
            assert len(db.execute(sql)) == 0
