#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_detailed.py file.

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
from subprocess import check_call, run
from .collectors import Collectors
from ..detailed_mrt_file import Detailed_MRT_File
from ..mrt_parser import MRT_Parser
from ..mrt_types import MRT_Types
from ..mrt_detailed import MRT_Detailed
from ..detailed_tables import MRT_Detailed_Table
from ...utils import utils
from ...database import Database


@pytest.mark.mrt_detailed
class Test_MRT_Detailed:
    """Tests all functions within the mrt detailed class."""

    def setup(self):
        """NOTE: For all of your tests, run off a single time.

        Do NOT get the default start and end after every test.
        The reason being that the day could change, then the times will
        differ.
        """
        # Set times for testing purposes
        # Or: 06/17/2020 @ 21:00:00
        self._start = 1592427600
        # Or: 06/17/2020 @ 23:59:59
        self._end = 1592438399

    @pytest.mark.back
    def test_backslashes(self):
        utils.run_cmds("echo 192.168.0.1 | sed 's/\./test\\ttest/g' > back.txt")

    def test__init__(self):
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
                    MRT_Detailed()
                    # If no warning was given even though it should have
                    if not record:
                        pytest.fail("Warning not issued when deps not installed")
            # No need to install anything
            else:
                # Run init
                MRT_Detailed()
            # Check that the table exists and is empty
            assert db.execute("SELECT * FROM mrt_detailed") == []

    @pytest.mark.urls
    @pytest.mark.parametrize("sources, collectors, api_param",
                             [(MRT_Types, 85, Collectors.collectors_1.value),
                              (MRT_Types, 170, Collectors.collectors_2.value),
                              (MRT_Types, 255, Collectors.collectors_3.value),
                              ([], 0, Collectors.collectors_0.value),
                              ([MRT_Types.routeviews], 2295, {}),
                              ([MRT_Types.ris], 5082, {}),
                              (MRT_Types, 7377, {})])
    def test_get_caida_mrt_urls(self,
                                sources,
                                collectors,
                                api_param,):
        """Tests getting caida data.
        """

        urls = []
        # Create a parser
        test_parser = MRT_Detailed()
        # Get our URLS
        urls = test_parser._get_caida_mrt_urls(sources,
                                               self._start,
                                               self._end,
                                               api_param)
        # If we have no sources, then urls should be empty.
        if sources == []:
            assert urls == []
        # Verify we have valid URLs
        for url in urls:
            assert validators.url(url[0])
        # Verify expected collectors == #urls
        assert len(urls) == collectors
        return urls

    @pytest.mark.mt_down
    def test_multiprocess_download(self, url_arg=None):
        parser = MRT_Detailed()
        urls = url_arg if url_arg is not None else(
               self.test_get_caida_mrt_urls([MRT_Types.routeviews],
                                            85,
                                            Collectors.collectors_1.value))
        mrt_files = parser._multiprocess_download(5, urls)
        assert len(mrt_files) == len(urls)
        parser._multiprocess_download(5, urls)
        no_multi = parser._multiprocess_download(1, urls)
        assert len(no_multi) == len(mrt_files)
        return mrt_files

    @pytest.mark.mt_parse
    def test_multiprocess_parse_dls(self, scanner=True):
        with Database() as db:
            db.execute("""DROP TABLE IF EXISTS mrt_detailed""")
        parser = MRT_Detailed()
        urls = self.test_get_caida_mrt_urls([MRT_Types.routeviews],
                                            26,
                                            Collectors.collectors_1.value)
        mrt_files = self.test_multiprocess_download(urls)
        expected_lines = self._get_total_number_of_lines(mrt_files)
        with Database() as db:
            print(db.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_name = 'mrt_detailed';"))
            parser._multiprocess_parse_dls(10, mrt_files, scanner)
            db_lines = db.execute("SELECT COUNT(*) FROM mrt_detailed")
            lines = db_lines[0]['count']
            assert lines == expected_lines
            return lines

    # Remove these when done
    @pytest.mark.getbash
    def test_getbash(self):
        from ..mrt_file import MRT_File 
        with open('../dumps/bashargs.txt', 'w+') as f:
            f.write(MRT_File('x','x','x', 1)._bgpscanner_args())

    @pytest.mark.nullinsert
    def test_nullinsert(self):
        path = '../dumps/edited.csv'
        utils.csv_to_db(MRT_Detailed_Table, path)

    @pytest.mark.show_cmds
    def test_show_cmds(self):
        x = Detailed_MRT_File('x', 'x', 'x', 159.20, 159.45)._bgpscanner_args()
        x = x.split(' | ')
        x.pop(0)
        utils.run_cmds('cp ../dumps/one_line.csv ../dumps/one_line_copy.csv')
        test_file = '../dumps/one_line_copy.csv'
        alternative = '../dumps/one_line_copy2.csv'
        alternate = True
        for c in x:
            print(c)
            if alternate:
                c1 = f'cat {test_file} | {c} > {alternative}'
                alternate = False
            else:
                c1 = f'cat {alternative} | {c} > {test_file}'
                alternate = True
            utils.run_cmds(c1)
            if alternate:
                with open(test_file, 'r') as f:
                    print(f.read())
            else:
                with open(alternative, 'r') as f:
                    print(f.read())
        

##################
#Helper Functions#
##################

    def _get_total_number_of_lines(self, mrt_files, bgpscanner=True):
        test_path = "/tmp/testfile.txt"
        utils.delete_paths(test_path)
        f = open(test_path, "w")
        f.close()
        for mrt_file in mrt_files:
            tool = "bgpscanner" if bgpscanner else "bgpdump"
            bash_args = '{} {} '.format(tool, mrt_file.path)
            bash_args += ">> {}".format(test_path)
            print(bash_args)
            check_call(bash_args, shell=True)
        num_lines = utils.get_lines_in_file(test_path)
        utils.delete_paths(test_path)
        return num_lines
