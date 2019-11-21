#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_file.py file.

For specifics on each test, see docstrings under each function.
"""

from ..relationships_file import Rel_File, Rel_Types
from ..relationships_parser import Relationships_Parser
from ..tables import Customer_Providers_Table, Peers_Table
from ..tables import ROVPP_Customer_Providers_Table, ROVPP_Peers_Table
from ...utils import utils, db_connection


__author__ = "Matt Jaccino", "Justin Furuness"
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_Relationships_File:
    """Tests all local functions within the Relationships File class."""

    def setup(self):
        """Set up a Relationships File object with the Relationships Parser.

        This is to get the necessary arguments to intialize the File object.
        """

        # Initialize a Relationships Parser object
        self.rel_par = Relationships_Parser()
        # Initialize Relationships File object
        self.rel_file = Rel_File(self.rel_par.path,
                                 self.rel_par.csv_dir,
                                 self.rel_par._get_urls()[0],  # Gets URL
                                 self.rel_par.logger)

    def test__db_insert(self):
        """Tests the _db_insert function"""

        # Download a file to use as a test
        utils.download_file(self.rel_file.logger,
                            self.rel_file.url,
                            self.rel_file.path)
        # Unzip this file and assign its new path
        self.rel_file.path = utils.unzip_bz2(self.rel_file.logger,
                                             self.rel_file.path)
        peer_count, cust_prov_count = self._get_lines(self.rel_file.path)

        # Clean up with utils so as not to contaminate test
        utils.delete_paths(self.rel_file.logger,
                           [self.rel_file.csv_dir, self.rel_file.path])
        self.rel_par.parse_files()

        # Make sure the counts are accurate
        with db_connection(Peers_Table) as peers:
            assert peer_count == peers.get_count()
        with db_connection(Customer_Providers_Table) as cust_provs:
            assert cust_prov_count == cust_provs.get_count()

    def test__get_rel_attributes(self):
        """Tests the _get_rel_attributes function"""

        # Grep call for finding peer relationships:
        # All lines not containing '-1' or '#', delimited by tabs
        peers_grep = 'grep -v "\\-1" | grep -F -v "#" | cut -d "|" -f1,2'
        peers_grep += ' | sed -e "s/|/\t/g"'
        # Grep call for finding customer-provder relationships:
        # All lines containing '-1' but not '#", delimited by tabs
        cust_prov_grep = 'grep "\\-1" | grep -F -v "#" | cut -d "|"'
        cust_prov_grep += ' -f1,2 | sed -e "s/|/\t/g"'
        # Expected return value for 'grep' from this method
        exp_grep = {Rel_Types.CUSTOMER_PROVIDERS: cust_prov_grep,
                    Rel_Types.PEERS: peers_grep}
        # CSV for 'peers'
        peers_csv = self.rel_file.csv_dir+'/rel.csv'
        # CSV for 'customer_providers'
        cust_prov_csv = self.rel_file.csv_dir+'/rel.csv'
        # Expected return value for 'csvs' from this method
        exp_csvs = {Rel_Types.CUSTOMER_PROVIDERS: cust_prov_csv,
                    Rel_Types.PEERS: peers_csv}
        # Assume rovpp == False for table attributes call, since it makes
        # no difference for testing this method
        table_attr = {Rel_Types.CUSTOMER_PROVIDERS: Customer_Providers_Table,
                      Rel_Types.PEERS: Peers_Table}
        # Finally, make sure all output matches what is expected
        assert self.rel_file._get_rel_attributes() == \
            (exp_grep, exp_csvs, table_attr)

    def test__get_table_attributes(self):
        """Tests the _get_table_attributes function"""

        # Expected output for call with rovpp == False.
        rovpp_false = {Rel_Types.CUSTOMER_PROVIDERS: Customer_Providers_Table,
                       Rel_Types.PEERS: Peers_Table}
        # Expected output for call with rovpp == True.
        rovpp_true = {Rel_Types.CUSTOMER_PROVIDERS:
                      ROVPP_Customer_Providers_Table,
                      Rel_Types.PEERS: ROVPP_Peers_Table}
        # Make sure both calls give expected output.
        assert self.rel_file._get_table_attributes(rovpp=False) == rovpp_false
        assert self.rel_file._get_table_attributes(rovpp=True) == rovpp_true

########################
### Helper Functions ###
########################

    def _get_lines(self, path):
        """Returns total number of lines in the file"""

        with open(path) as sample:
            peer_count = 0
            cust_prov_count = 0
            for line in sample:
                if "|0|" in line:
                    peer_count += 1
                elif "|-1|" in line:
                    cust_prov_count += 1
        return peer_count, cust_prov_count
