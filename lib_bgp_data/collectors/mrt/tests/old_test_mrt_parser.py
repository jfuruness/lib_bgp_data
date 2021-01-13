#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_parser.py file.

For speciifics on each test, see the docstrings under each function.
Note that if tests are failing, the self.start and self.end may need
updating to be more recent. Possibly same with the api_param_mods.
"""


from multiprocessing import cpu_count
import os
import requests
from subprocess import check_call
import validators
from ..mrt_file import MRT_File
from ..mrt_parser import MRT_Parser
from ..mrt_sources import MRT_Sources
from ..tables import MRT_Announcements_Table
from ...utils import utils
from ...utils.database import Database

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class OLD_Test_MRT_Parser:
    """Tests all functions within the mrt parser class."""

    def setup(self):
        """Inits member variables to be used everywhere"""

        # Put here because at some point they will be outdated
        # So here it is a one line fix
        self._start = 1572613200
        self._end = 1572616800
        # Two are used to test for multiprocessing
        # Two are also used to limit the number of files and reduce runtime
        self._api_param_mods = {"collectors[]": ["route-views.telxatl",
                                                 "route-views2"]}
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

    def test_get_caida_mrt_urls(self, parser=None, param_mods=True):
        """Tests the get_mrt_urls function with api parameters specifically
        for the CAIDA URLs, since the other tests will use these to cut
        runtime.  The Isolario URLs are tested seperately

        This makes sure it returns the proper data for the request. This
        is done through first querying the api and getting the debug
        information. That information is later checked against the total
        number urls in the return of the _get_mrt_urls function.

        """

        # Creates parser
        parser = parser if parser else MRT_Parser()
        # For when there are no param mods
        api_param_mods = self._api_param_mods if param_mods else {}
        # Gets the total number of mrt files
        num_files = self._get_num_mrt_files(self._start,
                                            self._end,
                                            api_param_mods)
        # Everything but isolario
        sources = [x for x in MRT_Sources.__members__.values()
                   if x != MRT_Sources.ISOLARIO]
        # Gets all the mrt file urls
        mrt_file_urls = parser._get_mrt_urls(self._start,
                                             self._end,
                                             api_param_mods,
                                             sources=sources)
        # Checks that the number of urls is correct
        assert len(mrt_file_urls) == num_files
        # Now compare when including Isolario URLs
        mrt_file_urls_iso = parser._get_mrt_urls(self._start,
                                                 self._end,
                                                 api_param_mods)
        # Makes sure that all of them are actually urls
        for url in mrt_file_urls_iso:
            assert validators.url(url)
        return mrt_file_urls

    def _get_mrt_urls(self, parser=None, param_mods=True):
        """Gets all MRT URLs from CAIDA and Isolario."""

        return self.test_get_caida_mrt_urls(parser, param_mods) + \
            self.test_get_mrt_urls_iso()

    def test_get_mrt_urls_no_param_mods(self):
        """Tests the get_mrt_urls function without api parameters.

        For a more in depth explanation, see the test_get_mrt_urls func.
        """

        num_files = self._get_num_mrt_files(self._start,
                                            self._end)
        mrt_file_urls = self._get_mrt_urls(param_mods=False)
        assert len(mrt_file_urls) == num_files and len(mrt_file_urls) >= 40

    def test_get_mrt_urls_iso(self):
        """Tests the get_mrt_urls_iso function which should return a list
        of URLs from the Isolario.it page under each of its different
        subdirectories."""

        # Initialize a parser object
        parser = MRT_Parser()
        # Get MRT Files
        mrt_file_urls = parser._get_mrt_urls(self._start, self._end, sources=[MRT_Sources.ISOLARIO])
        # Each of the 5 subdirectories contain a folder for the each month
        # and from each folder we only want one rib closest to the start
        # of the time interval but not if it is after the end
        assert 0 < len(mrt_file_urls) <= 5
        # Make sure each element of the list returned is a valid URL
        for url in mrt_file_urls:
            assert validators.url(url)
        return mrt_file_urls

    def test_multiprocess_download(self,
                                   parser=None,
                                   clean=False,
                                   param_mods=True):
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
        urls = self.test_get_mrt_urls(parser, param_mods)
        # Download mrt files
        mrt_files = parser._multiprocess_download(3, urls)
        # Makes sure the mrt files are the same length as the urls
        assert len(mrt_files) == len(urls)
        # Makes sure all mrt files where downloaded
        for mrt_file in mrt_files:
            assert os.path.exists(mrt_file.path)
        # Deletes all the files if clean is passed
        if clean:
            utils.delete_paths(None, [x.path for x in mrt_files])
        return mrt_files

    def test_multiprocess_download_no_params(self):
        """Test the multiprocess download without api parameters.

        For more in-depth explanation, see test_multiprocess_download func.
         """

        self.test_multiprocess_download(param_mods=False)

    def test_singular_vs_multiprocess_dl(self):
        """Compares the outputs of single process vs. multiprocess
        downloading of MRT files.

        This test will take a long time as it checks both with and
        without api parameters.
        """

        # Get the URLs with api parameters
        urls_param_mods = self.test_get_mrt_urls(param_mods=True)
        # Get all of the URLs
        urls_no_param_mods = self.test_get_mrt_urls(param_mods=False)
        # Download using a single process
        singular_mods = self._single_process_download(urls_param_mods)
        # Download using multiprocessing
        multi_mods = self.test_multiprocess_download(param_mods=True)
        # Make sure both give the same output and have elements
        assert len(singular_mods) == len(multi_mods)
        assert len(multi_mods) > 0
        # Make sure the file URLs match in the subsets
        singular_mods.sort(key=lambda f: f.url)
        multi_mods.sort(key=lambda f: f.url)
        i = 0
        while i < len(multi_mods):
            assert singular_mods[i].url == multi_mods[i].url
            i += 1
        # Download all with a single process
        singular_no_mods = self._single_process_download(urls_no_param_mods)
        # Download all with multiprocessing
        multi_no_mods = self.test_multiprocess_download(param_mods=False)
        # Make sure these also give the same output
        assert len(singular_no_mods) == len(multi_no_mods)

    def test_multiprocess_parse_dls(self,
                                    bgpscanner=True,
                                    param_mods=True):
        """Tests the _multiprocess_parse_dls function with bgpscanner.

        This makes sure that the total number of files downloaded is the
        same as the urls. All files are also checked to see if they
        downloaded. Afterwards they are deleted if clean is set to true.

        Note: If this test is failing later, it's possible the dates are
        outdated, or the api parameter mods.
        """

        # Initialize the parser
        parser = MRT_Parser()
        # Use earlier test to get MRT files
        mrt_files = self.test_multiprocess_download(parser=parser,
                                                    clean=False,
                                                    param_mods=param_mods)
        # Total lines from bgpscanner with no AS sets and no regex
        total_lines = self._get_total_number_of_lines(mrt_files)
        # Clear True calls clear_tables and then _create_tables
        with db_connection(MRT_Announcements_Table, clear=True) as db:
            # This errors from the amount of times the parser initialization
            # https://github.com/uqfoundation/pathos/issues/111
            # I tried the fixes suggested but it did not fix the problem
            # So now I just changed the number of threads every time
            # Parses all of the downloaded files
            parser._multiprocess_parse_dls(4, mrt_files, bgpscanner)
            # Makes sure all lines are inserted into the database
            # Also makes sure that the regex is accurate
            assert (select_all := db.get_count()) == total_lines
            # Checks to make sure that no values are null
            sqls = ["SELECT * FROM mrt_announcements WHERE prefix IS NULL",
                    "SELECT * FROM mrt_announcements WHERE as_path IS NULL",
                    "SELECT * FROM mrt_announcements WHERE origin IS NULL",
                    "SELECT * FROM mrt_announcements WHERE time IS NULL"]
            for sql in sqls:
                assert len(db.execute(sql)) == 0
            return db.get_all()

    def test_multiprocess_parse_dls_no_param_mods(self):
        """Tests the multiprocess_parse_dls with no api parameters.

        For a better explanation, see the test_multiprocess_parse_dls
        function.
        """

        self.test_multiprocess_parse_dls(param_mods=False)

    def test_multiprocess_parse_dls_bgpdump(self):
        """Tests the _multiprocess_parse_dls function with bgpdump.

        For a more in depth explanation, see the docstring in the
        test_multiprocess_parse_dls function.
        """

        self.test_multiprocess_parse_dls(bgpscanner=False)

    def test_singular_vs_multiprocess_parse_dls(self):
        """Compares outputs of singular vs multiprocess parsing of
        files.
        """

        # Parse with multiprocessing and store table entry count
        multi_params = len(self.test_multiprocess_parse_dls())
        # Parse again with a single process and store table entry count
        singular_params = \
            len(self._single_process_parse_dls(param_mods=True,
                                               bgpscanner=True))
        # Make sure these counts are the same
        assert multi_params == singular_params

    def test_single_vs_multiprocess_parse_dls_no_param_mods(self):
        """Test single vs. multiprocess parsing without api parameters"""

        # Repeat last test, but without using api parameters
        # Store the count of entries after multiprocess parsing
        multi_no_params = \
            len(self.test_muliprocess_parse_dls_no_param_mods())
        # Store count of entries after single process parsing
        singular_no_params = \
            len(self._single_process_parse_dls(param_mods=False,
                                               bgpscanner=True))
        # Make sure both entry counts are the same
        assert multi_no_params == singular_no_params

    def test_parse_files(self, param_mods=True):
        """Tests the parse_files function with IPV4=True, IPV6=True.

        Just combines all of the tests basically
        """

        api_param_mods = self._api_param_mods if param_mods else {}
        MRT_Parser().parse_files(api_param_mods=api_param_mods,
                                 IPV4=True,
                                 IPV6=True)
        with db_connection() as db:
            db.execute("SELECT * FROM mrt_announcements")

    def test_parse_files_no_param_mods(self):
        """Tests parse_files without api parameters.

        For a better explanation, see the test_parse_files function.
        """

        self.test_parse_files(param_mods=False)

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

    def _get_total_number_of_lines(self, mrt_files, bgpscanner=True):
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
        num_lines = utils.get_lines_in_file(test_file)
        # Deletes the files that we no longer need
        utils.delete_paths(None, test_path)
        return num_lines

    def _single_process_download(self, urls):
        """Downloads MRT files one at a time.

        Used as a baseline for multiprocess downloading.
        """

        # Use parser to get correct path and csv_dir
        parser = MRT_Parser()
        # Create MRT files for each URL
        mrt_files = [MRT_File(parser.path,
                              parser.csv_dir,
                              url,
                              i + 1,
                              len(urls),
                              parser.logger)
                     for i, url in enumerate(urls)]
        # Download each file individually
        for f in mrt_files:
            utils.download_file(f.logger, f.url, f.path, f.num,
                                f.total_files)
        # Return the list of files
        return mrt_files

    def _single_process_parse_dls(self, param_mods=True, bgpscanner=False):
        """Parses downloads one at a time.

        Used as a baseline for multiprocess parsing.
        """

        # Get MRT files from download test
        mrt_urls = self.test_get_mrt_urls()
        # Using the single process download since test failed with multi
        mrt_files = self._single_process_download(mrt_urls)
        # Establish a connection with the database
        with db_connection(MRT_Announcements_Table, clear=True) as db:
            # Parse each file individually
            for f in mrt_files:
                f.parse_file(bgpscanner)
            # Query the table for all entries
            select_all = db.execute("SELECT * FROM mrt_announcements")
        return select_all
