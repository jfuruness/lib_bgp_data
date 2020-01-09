#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""

from ..relationships_parser import Relationships_Parser
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

    def _test_example(self, hijack, hijack_type, peers, customer_providers, as_list, output):
        """tests example graphs from paper

        Input:
            hijack: hijack class, with ann info
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
