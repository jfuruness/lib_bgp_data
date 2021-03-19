#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_file.py file.

For specifics on each test, see the docstrings under each function.
"""


from subprocess import check_call

import pytest
from .expected_output import Expected_Output
from ..mrt_file import MRT_File
from ..mrt_parser import MRT_Parser
from ..tables import MRT_Announcements_Table
from .....utils.database import Database
from .....utils import utils

__authors__ = ["Matt Jaccino", "Justin Furuness", "Nicholas Shpetner"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"


@pytest.mark.mrt_parser
class Test_MRT_File:
    """This will test methods of the MRT_File class."""

    def test_bgpscanner_vs_bgpdump(self):
        """Compares the outputs of parsing an MRT file using bgpscanner
        with using bgpdump.

        NOTE: We actually need to do this for all of them. Why? Because
        incidentally bgpscanner is by defualt different than bgpdump.
        bgpscanner does not include malformed announcements, bgpdump
        does. When we install it, we change this feature. However,
        few files will have this problem, so we need to run it over all
        of them. You can prob have a shorter version of this test.

        Also note that the other reason we do this is to check between
        RIPE, Route-views, and ISOLARIO data
        """

        # A more comprehensive test over all URLs in test_mrt_parser
        # We get the sixth one for speed. The rest are isolario
        url = MRT_Parser()._get_mrt_urls()[5]
        # Create an MRT_File object and download from the URL above
        test_file: MRT_File = self._mrt_file_factory(url=url)
        _scanner_entries = self._get_entries(test_file, bgpscanner=True)
        # Create another MRT_File object and download
        test_file2: MRT_File = self._mrt_file_factory(url=url)
        # Get the number of entries in the table when parsed with BGPDump
        _dump_entries = self._get_entries(test_file2, bgpscanner=False)
        # Make sure both entries are identical
        assert _scanner_entries == _dump_entries

    def test_bgpscanner_regex(self):
        """This will test if the method '_bgpscanner_args' uses correct
        regex to get desired output from a file.
        """
        expected = Expected_Output()
        scanout = expected.get_scanner()
        # because doesn't delete files properlydon't let it run at all

        args = r' | cut -d "|" -f1,2,3,10 | sed -n "s/[=|+|-]|\([0|1|2|3|4|5'
        args += r'|6|7|8|9|%|\.|\:|a|b|c|d|e|f|/]\+\)|\([^{]*[[:space:]]\)*'
        args += r'\([^{]*\)|\(.*\)/\1\t{\2\3}\t\3\t\4/p"'
        args += ' | sed -e "s/ /, /g"'
        # I've added an example of BGPScanner output in this directory called
        # '.bgpscanner_out.txt', which I will use to compare to the
        # desired output
        expected_out = "1.2.3.0/24\t{12345, 6789, 0123, 12345, 67890}"
        expected_out += "\t67890\t1234567890"
        # Pipe the example output through the args and output to a new file
        sys_call = "echo '" + scanout + "' | "
        sys_call += "cat - " + args + " > bgpscanner_reg.txt"
        check_call(sys_call, shell=True)
        # Use this file to compare to the expected output
        with open("bgpscanner_reg.txt", 'r') as reg:
            regex_out = reg.read()
        # Slice off the \n for comparison
        assert regex_out[:-1] == expected_out
        # Delete CSV files when complete
        check_call("rm bgpscanner_reg.txt", shell=True)
        # Create an MRT File object to use to get output
        test_file = self._mrt_file_factory()
        # Create a text file of the CSV after modifying BGPScanner output
        test_file.csv_name = "scanner.txt"
        test_file._convert_dump_to_csv(bgpscanner=True)
        # Get the number of lines in this file
        lines = utils.get_lines_in_file("scanner.txt")
        # Delete the file once the lines have been counted
        check_call("rm scanner.txt", shell=True)
        # Get the number of entries in the MRT Announcements table
        entries = len(self._get_entries(self._mrt_file_factory()))
        # Make sure these values match
        assert lines == entries

    def test_bgpdump_regex(self):
        """This will test if the method '_bgpdump_args' uses correct regex
        to get desired output from a file.
        """
        # because doesn't delete files properlydon't let it run at all
        expected = Expected_Output()
        dumpout = expected.get_dump()
        args = r' | cut -d "|" -f2,6,7 | sed -e "/{.*}/d" -e "s/\(.*|.*|\)'
        args += r'\(.*$\)/\1{\2}/g" -e "s/ /, /g" -e "s/|/\t/g"'
        args += r' -e "s/\([[:digit:]]\+\)}/\1}\t\1/g"'
        # I've added an example of BGPDump's output in this directory called
        # '.bgpdump_out.txt', which I will use to compare to the desired output
        expected_out = "1234567890\t12.34.56.0/24\t{12345, 67890, "
        expected_out += "1234, 5678, 90}\t90"
        # Pipe the example output through the args and output to a new file
        sys_call = "echo '" + dumpout + "' | "
        sys_call += "cat - " + args + " > bgpdump_reg.txt"
        check_call(sys_call, shell=True)
        # Use this file to compare to the expected output
        with open("bgpdump_reg.txt", 'r') as reg:
            regex_out = reg.read()
        # Slice off the \n for comparison
        assert regex_out[:-1] == expected_out
        # Delete the CSV files when complete
        check_call("rm bgpdump_reg.txt", shell=True)
        # Create an MRT File object to use to get output
        test_file = self._mrt_file_factory()
        # Create a text file of the CSV after modifying BGPDump output
        test_file.csv_name = "dump.txt"
        test_file._convert_dump_to_csv(bgpscanner=False)
        # Get the number of lines in this file
        lines = utils.get_lines_in_file("dump.txt")
        # Delete the file once the lines have been counted
        check_call("rm dump.txt", shell=True)
        # Get the number of entries in the MRT Announcements table
        entries = len(self._get_entries(self._mrt_file_factory(),
                                        bgpscanner=False))
        # Make sure these values match
        assert lines == entries

    def test_for_as_sets(self):
        # Populate the database before testing
        self._mrt_file_factory().parse_file()
        # Make sure not AS pathes contain sets
        with Database() as db:
            assert db.execute("SELECT COUNT(*) FROM mrt_announcements"
                              )[0]["count"] > 0
            sql = "SELECT as_path FROM mrt_announcements;"
            # Check for sets by looking for the set notation
            assert "{" not in str(db.execute(sql))

########################
### Helper Functions ###
########################

    def _get_entries(self, mrt_file, bgpscanner=True):
        """Gets entries from MRT Announcements"""

        with MRT_Announcements_Table(clear=True) as db:
            mrt_file.parse_file(bgpscanner)
            return db.get_all()

    def _mrt_file_factory(self,
                          start=utils.get_default_start(),
                          end=utils.get_default_end(),
                          url=None):
        """Generates MRT File objects with the same URL for comparison"""

        parser = MRT_Parser()
        url = parser._get_mrt_urls(start, end)[5] if not url else url
        mrt_file = MRT_File(parser.path,
                            parser.csv_dir,
                            url)
        utils.download_file(mrt_file.url, mrt_file.path)
        return mrt_file
