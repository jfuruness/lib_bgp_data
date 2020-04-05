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
from ..mrt_file import MRT_File
from ..mrt_parser import MRT_Parser
from ..mrt_sources import MRT_Sources
from ..tables import MRT_Announcements_Table
from ...utils import utils
from ...database import Database

@pytest.mark.mrt_parser
class Test_MRT_Parser:
    """Tests all functions within the mrt parser class."""

    def setup(self):
        """NOTE: For all of your tests, run off a single time.

        Do NOT get the default start and end after every test.
        The reason being that the day could change, then the times will
        differ.
        """
        # Set times for testing purposes, based off old tests
        # Nov 1, 2019, 1:00 PM
        self._start = 1572613200
        # Nov 1, 2019, 2:00 PM
        self._end = 1572616800
        # TODO: Check on how to set up param mods
        # I used the old _api_param_mods cause I don't quite
        # understand how it works.
        self._api_param_mods = {"collectors[]": ["route-views.telxatl",
                                                 "route-views2"]}
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
            else:
                # Run init
                MRT_Parser()
            # Check that the table exists and is empty
            assert db.execute("SELECT * FROM mrt_announcements") == []

    def test_get_iso_mrt_urls(self):
        """Tests getting isolario data.

        Should asser that when ISOLARIO not in sources it should
        return [].
        Should assert that there are 5 collectors by default.
        probably should parametize this function
        """
        # Create a parser
        test_parser = MRT_Parser()
        # Get our URLs
        # TODO: Ensure this works with how I set up param mods
        urls = test_parser._get_iso_mrt_urls(self._start, 
                                             self._end, 
                                             self._api_param_mods)
        # Assert that files is empty if ISOLARIO is not in sources
        if MRT_Sources.ISOLARIO not in sources:
            assert files == []
        # Verify that we have valid URLs
        for url in urls:
            assert validators.url(url)
        # Assert that we have 5 collectors
            assert len(urls) == 5
        

    def test_get_caida_mrt_urls(self):
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
        # TODO: This will fail since I am not calling it correctly. Check how to.
        urls = test_parser._get_caida_mrt_urls(self._start, 
                                               self._end, 
                                               self._api_param_mods)
        # If we have no URLs, then urls should be empty.
        if MRT_Sources.RIPE not in sources and MRT_Sources.ROUTE_VIEWS not in sources:
           assert urls == []
        # Verify we have valid URLs
        for url in urls:
           assert validators.url(url)
        # TODO: Figure out how to check number of collectors.

    def test_get_mrt_urls(self):
        """Tests getting url data.

        Assert that there is 47 total collectors. Also test param mods.
        Probably should parametize this function.
        """
        # Create the parser
        test_parser = MRT_Parser()
        # Call get mrt urls
        # Only needs three args given, I think, as last is call.
        urls = test_parser._get_mrt_urls(self._start,
                                         self._end,
                                         self._api_param_mods)
        # Ensure we have proper URLs
        for url in urls:
            assert validators.url(url)
        # Ensure we have 47 collectors...that's 47 URLs, right?
        assert len(urls) == 47
        # TODO: Test param mods


    def test_multiprocess_download(self):
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
        urls = parser._get_mrt_urls(self._start,
                                    self._end,
                                    self._api_param_mods)
        # Get a few (3) MRT files
        mrt_files = parser._multiprocess_download(3, urls[:2])
        # Test all files were downloaded correctly
        assert len(mrt_files) == 3
        # Test using more threads than necessary doesn't crash things
        parser._multiprocess_download(4, urls[:2])
        # Test no multiprocessing, check end result
        no_multi = parser._multiprocess_download(1, urls[:2])
        assert all(x in mrt_files for x in no_multi) 


    @pytest.mark.skip(reason="New hire work")
    def test_multiprocess_parse_dls(self):
        """Test multiprocess parsing of files

        NOTE: Run this with just a few quick URLs
            -in other words not from isolario
        Test that changing number of threads doesn't break it.
        Test that all files are parsed correctly. Do this by determining
        the total output of all files, and make sure that the database has
        that number of announcements in it.
        Test that the end result would be the same without multiprocessing.
        """
        """
        # Create the parser
        parser = MRT_Parser()
        # Get URLs
        urls = parser._get_mrt_urls(self._start,
                                    self._end,
                                    self._api_param_mods)
        # Get a few MRT files
        mrt_files = parser._multiprocess_download(3, urls[:2])
        with db_connection(MRT_Announcements_Table, clear = True) as db:
        """
        # TODO: Understand exactly what is going on, and how to test.
        pass

    @pytest.mark.skip(reason="New hire work")
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

        pass
    @pytest.mark.skip(reason="Broken at the moment")
    def test_filter_and_clean_up_db(self):
        """Tests that this function runs without error.

        No need to duplicate tests in tables.py. Make it fast.
        """
        # Make our parser
        parser = MRT_Parser()
        # Do what is necessary to create a table to filter and clean.
        urls = parser._get_mrt_urls(self._start,
                                    self._end,
                                    self._api_param_mods)
        files = parser._multiprocess_download(5, urls[:10])
        parser._multiprocess_parse_dls(5, files, True)
        # Hope that we don't run into an error here.
        parser._filter_and_clean_up_db(True, True)

    def  test_parse_files(self):
        """Test that the parse files function

        Should raise a warning and parse correctly. Use API Params
        and sources to ensure a fast runtime.
        """
        # Make a parser
        parser = MRT_Parser()
        # Call and see if we get a deprecated warn.
        with pytest.deprecated_call():
            parser.parse_files(self._start, 
                               self._end, 
                               self._api_param_mods)
