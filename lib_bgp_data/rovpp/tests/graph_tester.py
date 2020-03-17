#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""

from ...relationships_parser import Relationships_Parser
from ...relationships_parser.tables import ROVPP_Peers_Table, ROVPP_Customer_Providers_Table, ROVPP_ASes_Table
from ..rovpp_simulator import ROVPP_Simulator
from ..enums import Hijack_Types
from ..tables import Hijack, ROVPP_MRT_Announcements_Table#, Subprefix_Hijack_Table
from ...utils import Database, db_connection, utils
from ...extrapolator.tables import ROVPP_Extrapolation_Results_Table
from ...extrapolator import Extrapolator
from ..enums import Conditions as Conds

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Graph_Tester:
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
        utils.set_common_init_args(self, {})
        csvs = ["peers", "customer_providers", "ases", "exr_output"]
        rows = [peers, customer_providers, as_list, output]
        tables = [ROVPP_Peers_Table, ROVPP_Customer_Providers_Table, ROVPP_ASes_Table, ROVPP_Extrapolation_Results_Test_Table]

        csv_path = "/tmp/rovpp_tests/"
        utils.clean_paths(self.logger, [csv_path])
        for csv, rows, table in zip(csvs, rows, tables):
            utils.rows_to_db(self.logger,
                             rows,
                             "{}{}.csv".format(csv_path, csv),
                             table,
                             clear_table=True)
        # Then creates subprefix hijac table, which creates attackers and victims
        with db_connection(ROVPP_MRT_Announcements_Table, self.logger) as db:
            db.populate_mrt_announcements(hijack, hijack_type)
        # Runs rov++ with our custom table names
        Extrapolator().run_rovpp(hijack, table_names=["rovpp_ases"])
        with db_connection() as db:
            sql = """SELECT * FROM rovpp_extrapolation_results_test
                  EXCEPT
                  SELECT * FROM rovpp_extrapolation_results"""
            assert len(db.execute(sql)) == 0
            sql = """SELECT * FROM rovpp_extrapolation_results
                  EXCEPT
                  SELECT * FROM rovpp_extrapolation_results_test"""
            assert len(db.execute(sql)) == 0
