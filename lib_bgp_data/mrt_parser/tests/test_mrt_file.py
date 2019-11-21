#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_file.py file.

For specifics on each test, see the docstrings under each function.
"""

from ..mrt_file import MRT_File
from ..mrt_parser import MRT_Parser
from ...utils import utils, db_connection
from ..tables import MRT_Announcements_Table
<<<<<<< HEAD
from subprocess import check_call
=======
from subprocess import call
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822

__author__ = "Matt Jaccino"
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Test_MRT_File:
    """This will test methods of the MRT_File class."""

    def test_bgpscanner_vs_bgpdump(self):
        """Compares the outputs of parsing an MRT file using bgpscanner
        with using bgpdump.
        """

        # Create an MRT_File object and download from the URL above
        test_file = self._mrt_file_factory()
        scanner = self._get_entries(test_file, bgpscanner=True)
        # Create another MRT_File object and download
        test_file2 = self._mrt_file_factory()
        # Get the number of entries in the table when parsed with BGPDump
<<<<<<< HEAD
=======
        #
        # BGPDUMP FAILS
        #
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        dump = self._get_entries(test_file2, bgpscanner=False)
        # Make sure both entries are identical
        assert scanner == dump

    def test_bgpscanner_regex(self):
        """This will test if the method '_bgpscanner_args' uses correct
        regex to get desired output from a file.
        """

        args = ' | cut -d "|" -f1,2,3,10 | sed -n "s/[=|+|-]|\([0|1|2|3|4|5'
        args += '|6|7|8|9|%|\.|\:|a|b|c|d|e|f|/]\+\)|\([^{]*[[:space:]]\)*'
        args += '\([^{]*\)|\(.*\)/\\1\\t{\\2\\3}\\t\\3\\t\\4/p"'
        args += ' | sed -e "s/ /, /g"'
        # I've added an example of BGPScanner output in this directory called
        # '.bgpscanner_out.txt', which I will use to compare to the
        # desired output
        expected_out = "1.2.3.0/24\t{12345, 6789, 0123, 12345, 67890}"
        expected_out += "\t67890\t1234567890"
        # Pipe the example output through the args and output to a new file
        sys_call = "cat .bgpscanner_out.txt" + args + " > bgpscanner_reg.txt"
<<<<<<< HEAD
        check_call(sys_call, shell=True)
=======
        call(sys_call, shell=True)
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        # Use this file to compare to the expected output
        with open("bgpscanner_reg.txt", 'r') as reg:
            regex_out = reg.read()
        # Slice off the \n for comparison
        assert regex_out[:-1] == expected_out
        # Delete CSV files when complete
<<<<<<< HEAD
        check_call("rm bgpscanner_reg.txt", shell=True)
=======
        call("rm bgpscanner_reg.txt", shell=True)
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        # Create an MRT File object to use to get output
        test_file = self._mrt_file_factory()
        # Create a text file of the CSV after modifying BGPScanner output
        test_file.csv_name = "scanner.txt"
        test_file._convert_dump_to_csv(bgpscanner=True)
        # Get the number of lines in this file
        lines = self._number_of_lines("scanner.txt")
        # Delete the file once the lines have been counted
<<<<<<< HEAD
        check_call("rm scanner.txt", shell=True)
=======
        call("rm scanner.txt", shell=True)
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        # Get the number of entries in the MRT Announcements table
        entries = len(self._get_entries(self._mrt_file_factory()))
        # Make sure these values match
        assert lines == entries

    def test_bgpdump_regex(self):
        """This will test if the method '_bgpdump_args' uses correct regex
        to get desired output from a file.
        """

        args = ' | cut -d "|" -f2,6,7 | sed -e "/{.*}/d" -e "s/\(.*|.*|\)'
        args += '\(.*$\)/\\1{\\2}/g" -e "s/ /, /g" -e "s/|/\t/g"'
        args += ' -e "s/\([[:digit:]]\+\)}/\\1}\t\\1/g"'
        # I've added an example of BGPDump's output in this directory called
        # '.bgpdump_out.txt', which I will use to compare to the desired output
        expected_out = "1234567890\t12.34.56.0/24\t{12345, 67890, "
        expected_out += "1234, 5678, 90}\t90"
        # Pipe the example output through the args and output to a new file
        sys_call = "cat .bgpdump_out.txt" + args + " > bgpdump_reg.txt"
<<<<<<< HEAD
        check_call(sys_call, shell=True)
=======
        call(sys_call, shell=True)
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        # Use this file to compare to the expected output
        with open("bgpdump_reg.txt", 'r') as reg:
            regex_out = reg.read()
        # Slice off the \n for comparison
        assert regex_out[:-1] == expected_out
        # Delete the CSV files when complete
<<<<<<< HEAD
        check_call("rm bgpdump_reg.txt", shell=True)
=======
        call("rm bgpdump_reg.txt", shell=True)
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        # Create an MRT File object to use to get output
        test_file = self._mrt_file_factory()
        # Create a text file of the CSV after modifying BGPDump output
        test_file.csv_name = "dump.txt"
        test_file._convert_dump_to_csv(bgpscanner=False)
        # Get the number of lines in this file
        lines = self._number_of_lines("dump.txt")
        # Delete the file once the lines have been counted
<<<<<<< HEAD
        check_call("rm dump.txt", shell=True)
=======
        call("rm dump.txt", shell=True)
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        # Get the number of entries in the MRT Announcements table
        entries = len(self._get_entries(self._mrt_file_factory(),
                                        bgpscanner=False))
        # Make sure these values match
        assert lines == entries

    def test_for_as_sets(self):
        # Populate the database before testing
        self._mrt_file_factory().parse_file()
        # Make sure not AS pathes contain sets
        with db_connection() as db:
            assert len(db.execute("SELECT * FROM mrt_announcements;")) > 0
            for entry in db.execute("SELECT as_path FROM mrt_announcements;"):
                # Check for sets by looking for set notation
<<<<<<< HEAD
                assert "{" not in str(entry)
=======
                assert "{" not in entry
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822

###############
### Helpers ###
###############

    def _number_of_lines(self, filename):
        """Short helper function to get the number of lines in a file"""
<<<<<<< HEAD
        with open(filename, 'r') as f:
            for count, line in enumerate(f):
        return count + 1
=======
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                count += 1
        return count
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822

    def _get_entries(self, mrt_file, bgpscanner=True):
        """Short helper function to get entries from MRT Announcements"""
        with db_connection(MRT_Announcements_Table, clear=True) as db:
            mrt_file.parse_file(bgpscanner)
            entries = db.execute("SELECT * FROM mrt_announcements;")
        return entries

    def _mrt_file_factory(self):
<<<<<<< HEAD
        """Generates MRT File objects with the same URL for comparison"""
=======
>>>>>>> 64a89db2aff06585491f2b5f053b60d59a7a0822
        parser = MRT_Parser()
        file_url = parser._get_mrt_urls(utils.get_default_start(),
                                        utils.get_default_end())[0]
        mrt_file = MRT_File(parser.path, parser.csv_dir,
                            file_url, 1, 1, parser.logger)
        utils.download_file(mrt_file.logger, mrt_file.url, mrt_file.path,
                            1, 1, 1)
        return mrt_file
