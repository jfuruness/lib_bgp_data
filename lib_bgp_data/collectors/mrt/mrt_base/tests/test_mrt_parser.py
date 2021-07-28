#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_parser.py file.

For speciifics on each test, see the docstrings under each function.
Note that if tests are failing, the self.start and self.end may need
updating to be more recent. Possibly same with the api_param_mods.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino, Nicholas Shpetner"]
__credits__ = ["Justin Furuness", "Matt Jaccino", "Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest
import validators
import os
import filecmp
from subprocess import check_call
from .collectors import Collectors
from ..mrt_file import MRT_File
from ..mrt_parser import MRT_Parser
from ..mrt_sources import MRT_Sources
from ..tables import MRT_Announcements_Table
from .....utils import utils
from .....utils.database import Database


@pytest.mark.mrt_parser
class Test_MRT_Parser:
    """Tests all functions within the mrt parser class."""

    def setup(self):
        """NOTE: For all of your tests, run off a single time.

        Do NOT get the default start and end after every test.
        The reason being that the day could change, then the times will
        differ.
        """
        # Set times for testing purposes
        self._start = 1592351995
        # 6/16/2020, 23:59:55
        self._end = 1592438399
        # 6/17/2020, 23:59:59

    # This test passes (as of 4 Apr 2020)
    # However, it is recommended to test on a machine where dependencies
    # are not installed.
    def test___init__(self):
        """Tests initialization of the MRT parser

        When dependencies are not installed, the install function
        should be called. (Mock this, don't duplicate install test)
        In addition, the mrt_announcement table should be cleared.
        """
        # Connect to database
        with Database() as db:
            # Check if we warned that the dependencies are not installed
            # First check if we need to install dependencies
            if not os.path.exists("/usr/bin/bgpscanner"):
                with pytest.warns(None) as record:
                    # MRT_Parser should emit a warning here
                    MRT_Parser()
                    # If no warning was given even though it should have
                    if not record:
                        pytest.fail("Warning not issued when deps not installed")
            # No need to install anything
            else:
                # Run init
                MRT_Parser()
            # Check that the table exists and is empty
            assert db.execute("SELECT * FROM mrt_announcements") == []

    @pytest.mark.parametrize("sources, collectors", [(MRT_Sources, 5),
                                                     ([], 5)])
    def test_get_iso_mrt_urls(self, sources, collectors):
        """Tests getting isolario data.

        Should asser that when ISOLARIO not in sources it should
        return [].
        Should assert that there are 5 collectors by default.
        probably should parametize this function
        """
        # Create a parser
        test_parser = MRT_Parser()
        # Get our URLs
        urls = test_parser._get_iso_mrt_urls(self._start, sources)
        # Assert that files is empty if ISOLARIO is not in sources
        if MRT_Sources.ISOLARIO not in sources:
            assert urls == []
        # Verify that we have valid URLs
        for url in urls:
            assert validators.url(url)
        # Assert that we have 5 (by default) collectors
            assert len(urls) == collectors

    @pytest.mark.parametrize("sources, collectors, api_param",
                             [(MRT_Sources, 1, Collectors.collectors_1.value),
                              (MRT_Sources, 2, Collectors.collectors_2.value),
                              (MRT_Sources, 3, Collectors.collectors_3.value),
                              ([], 0, Collectors.collectors_0.value),
                              ([MRT_Sources.ROUTE_VIEWS], 27, {}),
                              ([MRT_Sources.RIPE], 21, {}),
                              (MRT_Sources, 48, {})])
    def test_get_caida_mrt_urls(self, sources, collectors, api_param):
        """Tests getting caida data.

        Should assert that when sources is just routeview that there
        are X number of collectors.
        Should assert that when sources is just ripe that there
        are X number of collectors.
        Should assert that when sources is all of them there are X
        collectors
        Should test api parameters and make sure they work.
        Probably should parametize this function
        """
        # Create a parser
        test_parser = MRT_Parser()
        # Get our URLS
        urls = test_parser._get_caida_mrt_urls(self._start,
                                               self._end,
                                               sources,
                                               api_param)
        # If we have no sources, then urls should be empty.
        if MRT_Sources.RIPE not in sources and MRT_Sources.ROUTE_VIEWS not in sources:
            assert urls == []
        # Verify we have valid URLs
        for url in urls:
            assert validators.url(url)
        # Verify expected collectors == #urls
        assert len(urls) == collectors

    @pytest.mark.parametrize("sources, collectors, api_param",
                             [(MRT_Sources, 53, {})])
    def test_get_mrt_urls(self, sources, collectors, api_param):
        """Tests getting url data.

        Assert that there is 52 total collectors. Also test param mods.
        Probably should parametize this function.
        """
        # Create the parser
        test_parser = MRT_Parser()
        # Call get mrt urls
        urls = test_parser._get_mrt_urls(self._start,
                                         self._end,
                                         api_param,
                                         sources)
        # Ensure we have proper URLs
        for url in urls:
            assert validators.url(url)
        assert len(urls) == collectors
        return urls

    def test_multiprocess_download(self, url_arg=None):
        """Test multiprocess downloading of files

        NOTE: Run this with just a few quick URLs
            -in other words not from isolario
        Test that changing number of threads doesn't break it.
        Test that all files are downloaded correctly.
        Test that end result is same as no multiprocessing
        """
        # Create the parser
        parser = MRT_Parser()
        # Get URLs
        urls = url_arg if url_arg is not None else(
               self.test_get_mrt_urls([MRT_Sources.ROUTE_VIEWS],
                                      3,
                                      Collectors.collectors_3.value))
        # Get MRT files
        mrt_files = parser._multiprocess_download(3, urls)
        # Test all files were downloaded correctly
        assert len(mrt_files) == len(urls)
        # Test using more threads doesn't break things
        parser._multiprocess_download(5, urls)
        # Test no multiprocessing, check end result
        no_multi = parser._multiprocess_download(1, urls)
        # Sanity check
        assert len(no_multi) == len(mrt_files)
        return mrt_files

    def test_multiprocess_parse_dls(self, scanner=True):
        """Test multiprocess parsing of files

        NOTE: Run this with just a few quick URLs
            -in other words not from isolario
        Test that changing number of threads doesn't break it.
        Test that all files are parsed correctly. Do this by determining
        the total output of all files, and make sure that the database has
        that number of announcements in it.
        Test that the end result would be the same without multiprocessing.
        """
        # Create the parser
        parser = MRT_Parser()
        # Get URLs
        urls = self.test_get_mrt_urls([MRT_Sources.ROUTE_VIEWS],
                                      3,
                                      Collectors.collectors_3.value)
        # Get a few MRT files
        mrt_files = self.test_multiprocess_download(urls)
        # Get expected amount of lines from the files
        expected_lines = self._get_total_number_of_lines(mrt_files)
        print(str(expected_lines))
        with Database() as db:
            # Parse files
            parser._multiprocess_parse_dls(3, mrt_files, scanner)
            # Make sure all files were inserted
            db_lines = db.execute("SELECT COUNT(*) FROM mrt_announcements")
            lines = db_lines[0]['count']
            assert lines == expected_lines
            # Ok, return result
            return lines

    @pytest.mark.slow
    def test_bgpscanner_vs_bgpdump_parse_dls(self):
        """Tests bgpscanner vs bgpdump

        A while back we changed our tool to bgpscanner. This tool had
        to be modified so that it did not ignore malformed announcements.
        We want to ensure that the output of these tools are the same. To
        do this we must run them over all the input files, since only some
        files have these malformed announcements. Essentially, just run the
        parser twice. Once with bgpscanner and once with bgpdump. Store
        them into two separate database tables, and check that they are
        exactly the same.

        Also, don't wait while the test is running. Be working on other
        tasks, as this will take hours and hours.
        """
        scanner = self.test_multiprocess_parse_dls(True)
        dump = self.test_multiprocess_parse_dls(False)
        assert scanner == dump

    def test_filter_and_clean_up_db(self):
        """Tests that this function runs without error.

        No need to duplicate tests in tables.py. Make it fast.
        """
        # Make our parser
        parser = MRT_Parser()
        # Do what is necessary to create a table to filter and clean.
        urls = self.test_get_mrt_urls([MRT_Sources.ROUTE_VIEWS],
                                      3,
                                      Collectors.collectors_3.value)
        files = parser._multiprocess_download(5, urls)
        parser._multiprocess_parse_dls(5, files, True)
        # Hope that we don't run into an error here.
        parser._filter_and_clean_up_db(True, True)

    def test_parse_files(self):
        """Test that the parse files function

        Should raise a warning and parse correctly. Use API Params
        and sources to ensure a fast runtime.
        """
        # Make a parser
        parser = MRT_Parser()
        # Call and see if we get a deprecated warn.
        kwargs = dict({'start': self._start, 'end': self._end,
                       'api_param_mods': {}, 'download_threads': 1,
                       'parse_threads': 1, 'IPV4': True, 'IPV6': False,
                       'bgpscanner': True, 'sources': []})
        with pytest.deprecated_call():
            parser.parse_files(**kwargs)

########################
### Helper Functions ###
########################

    # From old test
    def _get_total_number_of_lines(self, mrt_files, bgpscanner=True):
        """Gets total number of entries with no as sets.
        A test file is created. Bgpscanner or bgpdump is used with a
        simple grep to remove AS sets. The total number of lines in
        this file is counted for the total number of entries in the
        original MRT files.
        """

        test_path = "/tmp/testfile.txt"
        utils.delete_paths(test_path)
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
            print(bash_args)
            check_call(bash_args, shell=True)
        num_lines = utils.get_lines_in_file(test_path)
        # Deletes the files that we no longer need
        utils.delete_paths(test_path)
        return num_lines
