#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_parser.py file.

For speciifics on each test, see the docstrings under each function.
Note that if tests are failing, the self.start and self.end may need
updating to be more recent. Possibly same with the api_param_mods.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

@pytest.mark.mrt_parser
class Test_MRT_Parser:
    """Tests all functions within the mrt parser class."""

    def setup(self):
        """NOTE: For all of your tests, run off a single time.

        Do NOT get the default start and end after every test.
        The reason being that the day could change, then the times will
        differ.
        """

        pass

    @pytest.mark.skip(reason="New hire will work on this")
    def test___init__(self):
        """Tests initialization of the MRT parser

        When dependencies are not installed, the install function
        should be called. (Mock this, don't duplicate install test)
        In addition, the mrt_announcement table should be cleared.
        """

        pass

    @pytest.mark.skip(reason="New hire will work on this")
    def test_get_iso_mrt_urls(self):
        """Tests getting isolario data.

        Should asser that when ISOLARIO not in sources it should
        return [].
        Should assert that there are 5 collectors by default.
        probably should parametize this function
        """

        pass

    @pytest.mark.skip(reason="New hire will work on this")
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

        pass

    @pytest.mark.skip(reason="New hire will work on this")
    def test_get_mrt_urls(self):
        """Tests getting url data.

        Assert that there is 47 total collectors. Also test param mods.
        Probably should parametize this function.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_multiprocess_download(self):
        """Test multiprocess downloading of files

        NOTE: Run this with just a few quick URLs
            -in other words not from isolario
        Test that changing number of threads doesn't break it.
        Test that all files are downloaded correctly.
        Test that end result is same as no multiprocessing
        """

        pass

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

    @pytest.mark.skip(reason="New hire work")
    def test_filter_and_clean_up_db(self):
        """Tests that this function runs without error.

        No need to duplicate tests in tables.py. Make it fast.
        """

        pass

    @pytest.mark.skip(reason="new hire work")
    def  test_parse_files(self):
        """Test that the parse files function

        Should raise a warning and parse correctly. Use API Params
        and sources to ensure a fast runtime.
        """
        pass
