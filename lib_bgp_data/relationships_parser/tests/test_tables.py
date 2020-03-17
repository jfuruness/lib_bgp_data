#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from psycopg2.errors import UndefinedTable
import pytest

from ..tables import Provider_Customers_Table, Peers_Table
from ..tables import ASes_Table, AS_Connectivity_Table
from ..relationships_file import Rel_File
from ..relationships_parser import Relationships_Parser
from ...utils import utils
from ...database import Generic_Table_Test


__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@pytest.mark.relationships_parser
class Test_Provider_Customers_Table(Generic_Table_Test):

    table_class = Provider_Customers_Table


@pytest.mark.relationships_parser
class Test_Peers_Table(Generic_Table_Test):

    table_class = Peers_Table

@pytest.mark.relationships_parser
class Test_ASes_Table(Generic_Table_Test):
    """This will test all methods within the ASes_Table class."""

    table_class = ASes_Table

    def test_clear_table(self):
        """This will test the 'clear_table' method."""

        
        # Communicate with database
        with ASes_Table() as _db:
            # Make sure the table exists before testing the method
            _db.get_count()
            # Use the method 'clear_table' to remove the rovpp_ases table
            _db.clear_table()
            # Attempt to query the now non-existent table
            try:
                # Try to raise error by querying the table
                _db.get_count()
                assert False
            except UndefinedTable:
                # Otherwise, it was cleared
                pass

    def test_fill_table(self):
        """This will test the 'fill_table' method."""

        with ASes_Table() as _db:
            _parser = Relationships_Parser()
            url = _parser._get_urls()[0]
            _parser.run(url=url)
            # Use the 'fill_table' method to populate the table with data
            _db.fill_table()
            # Get the count of rovpp_ases after filling
            _post = _db.get_count()
        # Use the Rel_File class and Relationships_Parser class to find
        # number of unique ASes in file manually
        assert _post == self._get_unique_ases_count()

    def _get_unique_ases_count(self):
        """Helper function to unique number of ases in file"""

        parser = Relationships_Parser()
        url = parser._get_urls()[0]
        rel_file = Rel_File(parser.path, parser.csv_dir, url)
        utils.download_file(rel_file.url, rel_file.path)
        path = utils.unzip_bz2(rel_file.path)

        # Use a set to hold ASes
        ases = set()
        with open(path) as _sample:
            for _line in _sample:
                # Skip all commented lines
                if '#' not in _line:
                    # Format is as1 | as2 | things we don't need
                    for _as in _line.split('|')[:2]:
                        # Add to the set of all ases
                        ases.add(_as)

        # Clean up with utils
        utils.delete_paths([rel_file.csv_dir, rel_file.path])
        return len(ases)

@pytest.mark.relationships_parser
class Test_AS_Connectivity_Table(Generic_Table_Test):
    """This will test all methods within the ROVPP_AS_Connectivity_Table
    class.
    For better explanations of the tests, see the docstrings under each test.
    """

    table_class = AS_Connectivity_Table

    def test_fill_table(self):
        """This will test the fill_table method of the class"""


        # Make sure count is accurate
        with ASes_Table() as _ases_db:
            _ases_db.fill_table()
            with self.table_class() as _conn_db:
                _conn_db.fill_table()
                count_sql = """SELECT COUNT(*)
                            FROM as_connectivity
                            WHERE connectivity = 0;"""
                # Should be more than 45k edge ASes
                assert _conn_db.get_count(count_sql) > 45000
                # Should be more then 65k ASes
                assert (_conn_as_count := _conn_db.get_count()) > 65000
                # Should be the same number of ases in both tables
                assert _ases_db.get_count() == _conn_as_count
