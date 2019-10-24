#!/usr/bin/env python3

"""This file contains tests for the relationships_file.py file.

For specifics on each test, see docstrings under each function.
"""

import pytest
from datetime import date
from ..relationships_file import Rel_File, Rel_Types
from ..relationships_parser import Relationships_Parser
from ..tables import Customer_Providers_Table, Peers_Table
from ..tables import ROVPP_Customer_Providers_Table, ROVPP_Peers_Table
from ...utils import utils, Config


class Test_Relationships_File:
    """Tests all local functions within the Relationships File class."""

    def setup(self):
        """Set up a Relationships File object with the Relationships Parser.

        This is to get the necessary arguments to intialize the File object.
        """

        # Initialize a Relationships Parser object
        self.rel_par = Relationships_Parser()
        # Use the Parser object to get the file URL
        url = self.rel_par._get_url()[0]
        # Initialize Relationships File object
        self.rel_file = Rel_File(self.rel_par.path,
                                 self.rel_par.csv_dir,
                                 url,
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
        with open(self.rel_file.path) as sample:
            peer_count = 0
            cust_prov_count = 0
            for line in sample:
                if "|0|" in line:
                    peer_count += 1
                elif "|-1|" in line:
                    cust_prov_count += 1
                else:
                    continue
        # Clean up with utils
        utils.delete_paths(self.rel_file.logger,
                           [self.rel_file.csv_dir, self.rel_file.path])
        # Initialize a 'peers' table and a 'customer_providers' table object
        peers = Peers_Table()
        cust_prov = Customer_Providers_Table()
        # Make sure file for counts above gets parsed and added to database
        Config(self.rel_par.logger).update_last_date(date(1, 1, 1))
        self.rel_par.parse_files()
        # Make sure the counts are accurate
        assert peer_count == peers.get_count()
        assert cust_prov_count == cust_prov.get_count()
        # Close database connections
        peers.close()
        cust_prov.close()

    def test__get_rel_attributes(self):
        """Tests the _get_rel_attributes function"""

        # Grep call for finding peer relationships:
        # All lines not containing '-1' or '#', delimited by tabs
        peers_grep = 'grep -v "\-1" | grep -F -v "#" | cut -d "|" -f1,2'
        peers_grep += ' | sed -e "s/|/\t/g"'
        # Grep call for finding customer-provder relationships:
        # All lines containing '-1' but not '#", delimited by tabs
        cust_prov_grep = 'grep "\-1" | grep -F -v "#" | cut -d "|"'
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
