#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_parser.py file.

For specifics on each test, see the docstrings under each function.
"""

import requests
import os
from multiprocessing import cpu_count
from subprocess import check_call
from ..mrt_parser import MRT_Parser
from ..tables import MRT_Announcements_Table
from ...utils import Database, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Test_MRT_Parser:
    """Tests all functions within the mrt parser class."""

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

    def test_get_mrt_urls(self):
        """Tests the get_mrt_urls function.

        This makes sure it returns the proper data for the request. This
        is done through first querying the api and getting the debug
        information. That information is later checked against the total
        number urls in the return of the _get_mrt_urls function.

        Note: If this test is failing later, it's possible the dates are
        outdated.
        """

        # Randomly selected
        start = 1559394000
        end = 1559397600

        # Get the total number of files from a separate query to the api
        num_files = self._get_num_mrt_files(start, end)
        mrt_file_urls = MRT_Parser()._get_mrt_urls(start, end)
        # Make the request from the parser and make sure number is the same
        assert len(mrt_file_urls) == num_files
        for url in mrt_file_urls:
            assert "http" in url

    def test_get_mrt_urls_param_mods(self):
        """Tests the get_mrt_urls function.

        This makes sure it returns the proper data for the request. This
        is done through first querying the api and getting the debug
        information. That information is later checked against the total
        number urls in the return of the _get_mrt_urls function.

        Note: If this test is failing later, it's possible the dates are
        outdated.
        """

        start = 1559394000
        end = 1559397600

        api_param_mods = {"collector": "route-views2", "types": ['ribs']}
        num_files = self._get_num_mrt_files(start, end, api_param_mods)
        mrt_file_urls = MRT_Parser()._get_mrt_urls(start, end, api_param_mods)
        assert len(mrt_file_urls) == num_files
        for url in mrt_file_urls:
            assert "http" in url

    def test_multiprocess_download(self):
        start = 1559394000
        end = 1559397600
        # Used to limit it to only two files
        api_param_mods = {"collectors": ["route-views.telxatl", "route-views2"]}
        download_threads = 2
        parser = MRT_Parser()
        urls = parser._get_mrt_urls(start, end, api_param_mods)
        mrt_files = parser._multiprocess_download(download_threads, urls)
        assert len(mrt_files) == len(urls)
        for mrt_file in mrt_files:
            assert os.path.exists(mrt_file.path)

    def test_multiprocess_parse_dls_bgpscanner(self):
        dl_threads = 3
        parse_threads = 2
        bgpscanner = True
        self._multiprocess_parse_dls(dl_threads, parse_threads, bgpscanner)

    def test_multiprocess_parse_dls_bgpdump(self):
        dl_threads = 4
        parse_threads = 3
        bgpscanner = False
        self._multiprocess_parse_dls(dl_threads, parse_threads, bgpscanner)


    def _multiprocess_parse_dls(self, dl_threads, parse_threads, bgpscanner):
        start = 1559394000
        end = 1559397600
        api_param_mods = {"collectors[]": ["route-views.telxatl", "route-views2"]}
        # Must be 3 or else:
        # https://github.com/uqfoundation/pathos/issues/111
        # Couldn't fix this in the code no matter what
        download_threads = dl_threads
        parse_threads = parse_threads
        parser = MRT_Parser()
        urls = parser._get_mrt_urls(start, end, api_param_mods)
        mrt_files = parser._multiprocess_download(download_threads, urls)
        test_path = "/tmp/testfile.txt"
        try:
            os.remove(test_path)
        except FileNotFoundError:
            pass
        for mrt_file in mrt_files:
            # Remove as sets
            tool = "bgpscanner" if bgpscanner else "bgpdump"
            bash_args = '{} {} | grep -v '.format(tool, mrt_file_path)
            bash_args += '"{"' 
            bash_args += ">> {}".format(test_path)
            print(bash_args)
            check_call(bash_args, shell=True)
        with open(test_path) as test_file:
            num_lines = sum(1 for line in test_file)
        os.remove(test_path)
        with db_connection(MRT_Announcements_Table) as db:
            db.clear_table()
            db._create_tables()
            parser._multiprocess_parse_dls(parse_threads, mrt_files, bgpscanner=bgpscanner)
            print(num_lines)
            print(len(db.execute("SELECT * FROM mrt_announcements")))
            assert len(db.execute("SELECT * FROM mrt_announcements")) == num_lines
            sqls = ["SELECT * FROM mrt_announcements WHERE prefix IS NULL",
                    "SELECT * FROM mrt_announcements WHERE as_path IS NULL",
                    "SELECT * FROM mrt_announcements WHERE origin IS NULL",
                    "SELECT * FROM mrt_announcements WHERE time IS NULL"]
            for sql in sqls:
                assert len(db.execute(sql)) == 0
            
    def itest_multiprocess_parse_dls_bgpdump(self):
        start = 1559394000
        end = 1559397600
        api_param_mods = {"collectors[]": ["route-views.telxatl", "route-views2"]}
        download_threads = parse_threads = cpu_count()
        parser = MRT_Parser()
        urls = parser._get_mrt_urls(start, end, api_param_mods)
        mrt_files = parser._multiprocess_download(download_threads, urls)
        parser._multiprocess_parse_dls(parse_threads, mrt_files, bgpscanner=False)

########################
### Helper Functions ###
########################

    def _get_num_mrt_files(self, start, end, param_mods={}):
        URL = "https://bgpstream.caida.org/broker/data"
        PARAMS = {'human': True,
                  'intervals': ["{},{}".format(start, end)],
                  'types': ['ribs']}
        PARAMS.update(param_mods)
        data = requests.get(url=URL, params=PARAMS).json()
        return data.get("queryParameters").get("debug").get("numFiles")
