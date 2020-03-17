#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the relationships_file.py file.
For specifics on each test, see docstrings under each function.
"""

import pytest
from ..relationships_file import Rel_File, Rel_Types
from ..relationships_parser import Relationships_Parser
from ..tables import Provider_Customers_Table, Peers_Table
from ...utils import utils


__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

@pytest.mark.relationships_parser
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
                                 self.rel_par._get_urls()[0])  # Gets URL

    def test__db_insert(self):
        """Tests the _db_insert function"""

        # Download a file to use as a test
        utils.download_file(self.rel_file.url,
                            self.rel_file.path)

        # Unzip this file and assign its new path
        self.rel_file.path = utils.unzip_bz2(self.rel_file.path)

        _peer_count, _cust_prov_count = self._get_lines(self.rel_file.path)

        # Clean up with utils so as not to contaminate test
        utils.delete_paths([self.rel_file.csv_dir, self.rel_file.path])

        # Make sure the counts are accurate
        with Peers_Table(clear=True) as _peers:
            with Provider_Customers_Table(clear=True) as _cust_provs:
                Relationships_Parser().run()
                assert _peer_count == _peers.get_count()
                assert _cust_prov_count == _cust_provs.get_count()

    def test__get_rel_attributes(self):
        """Tests the _get_rel_attributes function"""

        # Grep call for finding peer relationships:
        # All lines not containing '-1' or '#', delimited by tabs
        _peers_grep = ('grep -v "\-1" | grep -F -v "#" | cut -d "|" -f1,2'
                       ' | sed -e "s/|/\t/g"')
        # Grep call for finding customer-provder relationships:
        # All lines containing '-1' but not '#", delimited by tabs
        _cust_prov_grep = ('grep "\-1" | grep -F -v "#" | cut -d "|"'
                           ' -f1,2 | sed -e "s/|/\t/g"')
        # Expected return value for 'grep' from this method
        _exp_grep = {Rel_Types.PROVIDER_CUSTOMERS: _cust_prov_grep,
                     Rel_Types.PEERS: _peers_grep}
        # Assume rovpp == False for table attributes call, since it makes
        # no difference for testing this method
        _exp_table_attr = {Rel_Types.PROVIDER_CUSTOMERS:
                               Provider_Customers_Table,
                           Rel_Types.PEERS: Peers_Table}

        _grep, _csvs, _table_attr = self.rel_file._get_rel_attributes()

        # Finally, make sure all output matches what is expected
        assert (_grep, _table_attr) == (_exp_grep, _exp_table_attr)

    def test__get_table_attributes(self):
        """Tests the _get_table_attributes function"""

        # Expected output
        output = {Rel_Types.PROVIDER_CUSTOMERS: Provider_Customers_Table,
                  Rel_Types.PEERS: Peers_Table}
        # Make sure calls give expected output.
        assert self.rel_file._get_table_attributes() == output

    @pytest.mark.skip(reason="New hire will work on this")
    def test_parse_file(self):
        """This uses a hidden relationship file to test the grep commands

        We use a small example relationship file, for which we know the
        expected output. We check that the data in the db is equivalent to
        what we expect."""

        pass

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
