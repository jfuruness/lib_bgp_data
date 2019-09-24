#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_parser.py file.

For speciifics on each test, see the docstrings under each function.
Note that if tests are failing, the self.start and self.end may need
updating to be more recent. Possibly same with the api_param_mods.
"""

import requests
import os
from multiprocessing import cpu_count
from subprocess import check_call
import validators
from ..mrt_parser import MRT_Parser
from ..tables import MRT_Announcements_Table
from ...utils import Database, db_connection, delete_paths

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_MRT_Parser:
    """Tests all functions within the mrt parser class."""

    def __init__(self):
        """Inits member variables to be used everywhere"""

        # Put here because at some point they will be outdated
        # So here it is a one line fix
        self._start = 1559394000
        self._end = 1559397600
        # Two are used to test for multiprocessing
        # Two are also used to limit the number of files and reduce runtime
        self._api_param_mods{"collectors[]": ["route-views.telxatl",
                                              "route-views2"]}
        # This errors due to the amount of times the mrt parser is initialized
        # https://github.com/uqfoundation/pathos/issues/111
        # I tried the fixes suggested but it did not fix the problem
        # So now I just changed the number of threads every time
        # Parse threads
        self._p_threads = 1
        # Download threads
        self._dl_threads = 1

    def test_mrt_init_(self):
        """Tests the __init__ function of the mrt parser.

        This function should create an empty table.
        """

        # Connect to the database
        with db_connection(Database) as db:
            # Init the parser which inits the mrt_announcements table
            MRT_Parser()
            # Check to make sure the table exists and is empty
            assert db.execute("SELECT * FROM mrt_announcements") == []

    def test_get_mrt_urls(self, parser=None, param_mods=True):
        """Tests the get_mrt_urls function with api parameters.

        This makes sure it returns the proper data for the request. This
        is done through first querying the api and getting the debug
        information. That information is later checked against the total
        number urls in the return of the _get_mrt_urls function.

        Note: If this test is failing later, it's possible the dates are
        outdated, or the api parameter mods.
        """

        # Creates parser
        parser = parser if parser else MRT_Parser()
        # For when there are no param mods
        api_param_mods = self.api_param_mods if param_mods else {}
        # Gets the total number of mrt files
        num_files = self._get_num_mrt_files(self.start,
                                            self.end,
                                            api_param_mods)
        # Gets all the mrt file urls
        mrt_file_urls = parser._get_mrt_urls(self.start,
                                             self.end,
                                             api_param_mods)
        # Checks that the number of urls is the same as the num_files
        assert len(mrt_file_urls) == num_files
        # Makes sure that all of them are actually urls
        for url in mrt_file_urls:
            assert validators.url.url(url)
        return mrt_file_urls

    def test_get_mrt_urls_no_param_mods(self):
        """Tests the get_mrt_urls function without api parameters.

        For a more in depth explanation, see the test_get_mrt_urls func.
        """

        self.test_get_mrt_urls(param_mods=False)

    def test_multiprocess_download(self, parser=None, clean=True):
        """Tests the _multiprocess_download function.

        This makes sure that the total number of files downloaded is the
        same as the urls. All files are also checked to see if they
        downloaded. Afterwards they are deleted if clean is set to true.

        Note: If this test is failing later, it's possible the dates are
        outdated, or the api parameter mods
        """

        # Creates parser
        parser = parser if parser else MRT_Parser()
        # Api param mods used to limit to only one file
        urls = self.test_get_mrt_urls(parser)
        # This errors due to the amount of times the mrt parser is initialized
        # https://github.com/uqfoundation/pathos/issues/111
        # I tried the fixes suggested but it did not fix the problem
        # So now I just changed the number of threads every time
        self.dl_threads += 1
        # Download mrt files
        mrt_files = parser._multiprocess_download(self._dl_threads, urls)
        # Makes sure the mrt files are the same length as the urls
        assert len(mrt_files) == len(urls)
        # Makes sure all mrt files where downloaded
        for mrt_file in mrt_files:
            assert os.path.exists(mrt_file.path)
        # Deletes all the files if clean is passed
        if clean:
            utils.delete_paths(None, [path for path in mrt_files])
        return mrt_files

    def test_multiprocess_parse_dls(self, bgpscanner=True):
        """Tests the _multiprocess_parse_dls function with bgpscanner.

        This makes sure that the total number of files downloaded is the
        same as the urls. All files are also checked to see if they
        downloaded. Afterwards they are deleted if clean is set to true.

        Note: If this test is failing later, it's possible the dates are
        outdated, or the api parameter mods.
        """

        parser = MRT_Parser()
        mrt_files = self.test_multiprocess_download(parser, clean=False)
        # Total lines from bgpscanner with no AS sets and no regex
        total_lines = self._get_total_number_of_lines()
        # Clear True calls clear_tables and then _create_tables
        with db_connection(MRT_Announcements_Table, clear=True) as db:
            # This errors due to the amount of times the mrt parser is initialized
            # https://github.com/uqfoundation/pathos/issues/111
            # I tried the fixes suggested but it did not fix the problem
            # So now I just changed the number of threads every time
            self.p_threads += 1
            # Parses all of the downloaded files
            parser._multiprocess_parse_dls(self.p_threads, mrt_files, bgpscanner)
            # Makes sure all lines are inserted into the database
            # Also makes sure that the regex is accurate
            assert len(db.execute("SELECT * FROM mrt_announcements")) == num_lines
            # Checks to make sure that no values are null
            sqls = ["SELECT * FROM mrt_announcements WHERE prefix IS NULL",
                    "SELECT * FROM mrt_announcements WHERE as_path IS NULL",
                    "SELECT * FROM mrt_announcements WHERE origin IS NULL",
                    "SELECT * FROM mrt_announcements WHERE time IS NULL"]
            for sql in sqls:
                assert len(db.execute(sql)) == 0

    def test_multiprocess_parse_dls_bgpdump(self):
       """Tests the _multiprocess_parse_dls function with bgpdump.

        For a more in depth explanation, see the docstring in the
        test_multiprocess_parse_dls function.
        """

        self._multiprocess_parse_dls_test(bgpscanner=False)

    def test_parse_files(self):
        """Tests the parse_files function with IPV4=True, IPV6=True.

        Just combines all of the tests basically
        """

        # This errors due to the amount of times the mrt parser is initialized
        # https://github.com/uqfoundation/pathos/issues/111
        # I tried the fixes suggested but it did not fix the problem
        # So now I just changed the number of threads every time

        self._dl_threads += 1
        self.p_threads += 1
        MRT_Parser().parse_files(api_param_mods=self.api_param_mods,
                                 IPV4=True,
                                 IPV6=True)
        with db_connection(Database):
            db.execute("SELECT * FROM mrt_announcements WHERE")
            # check to make sure there are both families, then do two more tests
            
########################
### Helper Functions ###
########################

    def _get_num_mrt_files(self, start, end, param_mods={}):
        """Gets the total number of files from the debug information."""

        URL = "https://bgpstream.caida.org/broker/data"
        PARAMS = {'human': True,
                  'intervals': ["{},{}".format(start, end)],
                  'types': ['ribs']}
        PARAMS.update(param_mods)
        data = requests.get(url=URL, params=PARAMS).json()
        return data.get("queryParameters").get("debug").get("numFiles")

    def _get_total_number_of_lines(self, mrt_files):
        """Gets total number of entries with no as sets.

        A test file is created. Bgpscanner or bgpdump is used with a
        simple grep to remove AS sets. The total number of lines in
        this file is counted for the total number of entries in the
        original MRT files.
        """

        test_path = "/tmp/testfile.txt"
        utils.delete_paths(None, test_path)
        # This could be multithreaded to count into different files
        # But this should only be ever run once
        # And there are only two files. Idc.
        for mrt_file in mrt_files:
            # Remove as sets
            # Must do it this way or else complains about the "{"
            tool = "bgpscanner" if bgpscanner else "bgpdump"
            bash_args = '{} {} | grep -v '.format(tool, mrt_file.path)
            bash_args += '"{"'
            bash_args += ">> {}".format(test_path)
            check_call(bash_args, shell=True)
        # Gets the number of lines
        with open(test_path) as test_file:
            num_lines = sum(1 for line in test_file)
        # Deletes the files that we no longer need
        utils.delete_paths(None, test_path)
        return num_lines
