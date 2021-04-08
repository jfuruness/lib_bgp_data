#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_installer.py file.

For speciifics on each test, see the docstrings under each function.
Note that if tests are failing, the self.start and self.end may need
updating to be more recent. Possibly same with the api_param_mods.
"""

__authors__ = ["Justin Furuness", "Nicholas Shpetner"]
__credits__ = ["Justin Furuness", "Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest
import os
from .test_mrt_file import Test_MRT_File
from ..mrt_installer import MRT_Installer
from .....utils import utils


@pytest.mark.mrt_parser
class Test_MRT_Installer:
    """Tests all functions within the mrt installer class."""

    def test_install_dependencies(self):
        """Tests installation of dependencies
        Should be able to be called twice and not error
        Should test both bgpscanner and bgpdump to ensure they don't error
            -potentially borrow test from test_mrt_file for this
        """
        bin_pkgs = ["meson",
                    "cmake"]
        dpkg_pkgs = ["zlib1g-dev",
                     "libbz2-dev",
                     "liblzma-dev",
                     "liblz4-dev"]
        test_installer = MRT_Installer()
        test_installer._install_bgpscanner_deps()
        for pkg in bin_pkgs:
            out = os.popen("ls /usr/bin | grep " + pkg).read()
            assert out != ''
        for pkg in dpkg_pkgs:
            out = os.popen("dpkg -l | grep " + pkg).read()
            assert out != ''
        assert os.popen("ls /usr/local/bin | grep ninja").read() != ''

    def test_debug_scaninstall(self):
        test_installer = MRT_Installer()
        test_installer._download_and_modify_bgpscanner()

    def test_install_bgpscanner(self):
        """Tests installation of bgpscanner and dependencies

        First uninstall all dependencies listed.
        Then install all of them
        no files should be leftover
        Should be able to be called twice and not error
        Should test bgpscanner to ensure it doesn't error
            -potentially borrow test from test_mrt_file for this

        Should also assert that the lines in bgpscanner are changed
            -not sure how to do this with just an executable
            -potentially create an MRT file that has malformed announcements?
            -if you have trouble with this please contact me
        """
        installer = MRT_Installer()
        filetest = Test_MRT_File()
        self.test_install_dependencies()
        installer._install_bgpscanner()
        filetest.test_bgpscanner_regex()

    def test_install_bgpdump(self):
        """Tests installation of bgpdump and dependencies
        Should be able to be called twice and not error
        Should test bgpdump to ensure it doesn't error
            -potentially borrow test from test_mrt_file for this

        """

        installer = MRT_Installer()
        filetest = Test_MRT_File()
        installer._install_bgpdump()
        filetest.test_bgpdump_regex()
