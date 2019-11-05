#!/usr/bin/env python3

import pytest
from ..tables import Customer_Providers_Table, Peers_Table
from ..tables import ROVPP_Customer_Providers_Table, ROVPP_Peers_Table
from ..tables import ROVPP_ASes_Table, ROVPP_AS_Connectivity_Table
from ...utils import db_connection, utils
from ..relationships_file import Rel_File
from ..relationships_parser import Relationships_Parser
from psycopg2.errors import UndefinedTable


class Create_Tables:
    """This will test the '_create_tables' method for all Table classes
    that inherit from Database"""

    def teardown(self):
        self.table.close()


class Test_ROVPP_Customer_Providers_Table(Create_Tables):

    def setup(self):
        self.table = ROVPP_Customer_Providers_Table()

    def test_ROVPP_CPT_name(self):
        """This will test the name property of the class"""

        assert self.table.name == "rovpp_customer_providers"


class Test_ROVPP_Peers_Table(Create_Tables):

    def setup(self):
        self.table = ROVPP_Peers_Table()

    def test_ROVPP_PT_name(self):
        """This will test the name propery of the class"""

        assert self.table.name == "rovpp_peers"


class Test_ROVPP_ASes_Table(Create_Tables):
    """This will test all methods within the ROVPP_ASes_Table class."""

    def setup(self):
        """Prepartion work for each test."""

        # Initialize the ROVPP_ASes_Table object
        self.table = ROVPP_ASes_Table()

    def test_clear_table(self):
        """This will test the 'clear_table' method."""

        # Communicate with database
        with db_connection() as db:
            # Make sure the table exists before testing the method
            db.execute("SELECT 1 FROM rovpp_ases;")
            # Use the method 'clear_table' to remove the rovpp_ases table
            self.table.clear_table()
            # Attempt to query the now non-existent table
            try:
                # Try to raise error by querying the table
                db.execute("SELECT 1 FROM rovpp_ases;")
                cleared = False
            except UndefinedTable:
                # Otherwise, it was cleared
                cleared = True
        # Make sure the table was successfully cleared
        assert cleared

    def test_fill_table(self):
        """This will test the 'fill_table' method."""

        # Make sure rovpp_peers & rovpp_customer_providers tables are not
        # empty before testing by parsing files with rovpp == True
        parser = Relationships_Parser()
        url = parser._get_url()[0]
        parser.parse_files(rovpp=True, url=url)
        with db_connection() as db:
            # Get the count of rovpp_ases before filling
            pre = db.execute("SELECT COUNT(*) FROM rovpp_ases;")[0]['count']
            # Use the 'fill_table' method to populate the table with data
            self.table.fill_table()
            # Get the count of rovpp_ases after filling
            post = db.execute("SELECT COUNT(*) FROM rovpp_ases;")[0]['count']
        # Make sure the count was 0 before filling
        assert pre == 0
        assert post > 0
        # Use the Rel_File class and Relationships_Parser class to find
        # number of unique ASes in file manually
        rel_file, path = _rel_file_generator()
        # Use a set to hold ASes
        ases = set()
        with open(path) as sample:
            for line in sample:
                # Skip all commented lines
                if '#' in line:
                    continue
                else:
                    # Split '|' delimited lines
                    data = line.split('|')
                    # The first AS is at index 0
                    as1 = data[0]
                    # The second, at 1
                    as2 = data[1]
                    # Add either AS to dict if not already present
                    if as1 not in ases:
                        ases.add(as1)
                    if as2 not in ases:
                        ases.add(as2)
        # Clean up with utils
        utils.delete_paths(rel_file.logger, [rel_file.csv_dir,
                                             rel_file.path])
        # The expected count is the number of dict entries
        exp_count = len(ases)
        # Make sure all unique ASes are in this table
        assert post == exp_count


class Test_ROVPP_AS_Connectivity_Table(Create_Tables):
    """This will test all methods within the ROVPP_AS_Connectivity_Table
    class.

    For better explanations of the tests, see the docstrings under each test.
    """
    def setup(self):
        """Preparation work for testing the ROVPP_AS_Connectivity_Table
        class."""

        # Initialize an ROVPP_AS_Connectivity_Table object
        self.table = ROVPP_AS_Connectivity_Table()

    def test__create_tables(self):
        """This will test the '_create_tables' method of the class"""

        # Make sure count is accurate
        with db_connection() as db:
            conn_count = db.execute("""SELECT COUNT(*) FROM
                                           rovpp_as_connectivity;"""
                                    )[0]['count']
            as_count = db.execute("SELECT COUNT(*) FROM " +
                                  "rovpp_ases;")[0]['count']
        # Make sure every AS from rovpp_ases is in this table
        assert conn_count == as_count

    def test_get_ases_by_transitivity(self):
        """This will test the 'get_ases_by_transitivity' method"""

        # Communicate with database
        with db_connection() as db:
            # Get list of all ASes with zero connectivity
            zero_conn = db.execute("""SELECT * FROM rovpp_as_connectivity
                                      WHERE connectivity = 0;"""
                                   )[0]['asn']
            # Get list of all ASes with non-zero connectivity
            non_zero_conn = db.execute("""SELECT * FROM rovpp_as_connectivity
                                          WHERE connectivity > 0;"""
                                       )[0]['asn']
        # Make sure these two lists are the same as those returned by method
        assert zero_conn, non_zero_conn \
            == self.table.get_ases_by_transitivity()

    def test_get_top_100_ases(self):
        """ This will test the 'get_top_100_ases' method"""

        # Manually query database for first 100 ASes in descending order
        with db_connection() as db:
            man_top = [x['asn'] for x in
                       db.execute("""SELECT * FROM rovpp_as_connectivity
                                     ORDER BY connectivity DESC LIMIT 100""")]
        # Use the 'get_top_100_ases' method to compare
        method_top = self.table.get_top_100_ases()
        # Make sure these two lists are the same
        assert man_top == method_top

    def test_get_not_top_100_ases(self):
        """This will test the 'get_not_top_100_ases' method"""

        # Manually query database for the 'not top 100' ASes in descending
        # order
        with db_connection() as db:
            man_not_top = [x['asn'] for x in
                           db.execute("""SELECT * FROM rovpp_as_connectivity
                                         ORDER BY connectivity DESC OFFSET
                                         100""")]
        # Use the 'get_not_top_100_ases' method to compare
        method_not_top = self.table.get_not_top_100_ases()
        # Make sure these two lists are the same
        assert man_not_top == method_not_top


###############
### Helpers ###
###############

def _rel_file_generator():
    """Helper function to return a Rel_File object"""

    parser = Relationships_Parser()
    url = parser._get_url()[0]
    rel_file = Rel_File(parser.path, parser.csv_dir, url, parser.logger)
    utils.download_file(rel_file.logger, rel_file.url, rel_file.path)
    path = utils.unzip_bz2(rel_file.logger, rel_file.path)
    return rel_file, path
