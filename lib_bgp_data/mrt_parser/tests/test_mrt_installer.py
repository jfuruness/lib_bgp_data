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
from ...utils import utils

@pytest.mark.mrt_parser
class Test_MRT_Installer:
    """Tests all functions within the mrt installer class."""


    @pytest.mark.skip(reason="New hire will work on this")
    def test_install_dependencies(self):
        """Tests installation of dependencies

        First uninstall all dependencies listed.
        Then install all of them
        no files should be leftover
        Should be able to be called twice and not error
        Should test both bgpscanner and bgpdump to ensure they don't error
            -potentially borrow test from test_mrt_file for this
        """

        
        # TODO: How to uninstall lzma-dev
        cmds = ["sudo apt -y remove meson",
                "sudo apt -y remove zlib1g",
                "sudo apt -y remove zlib1g-dev",
                "sudo apt-get -y remove libbz2-dev",
                "sudo apt-get -y remove liblzma-dev",
                "sudo apt-get -y remove liblz4-dev",
                "sudo apt-get -y remove ninja-build",
                "pip3 uninstall meson",
                "sudo apt-get -y remove cmake"]
        utils.run_cmds(cmds)
        pkgs = ["meson",
                "zlib1g:",
                "zlib1g-dev",
                "libbz2-dev",
                "liblzma-dev",
                "liblz4-dev",
                "ninja-build",
                "cmake "]
       for pkg in pkgs:
            out = os.popen("dpkg -l | grep -F '" + pkg + "'").read()
            assert out == ''
       test_installer = MRT_Installer()
       test_installer._install_bgpscaner_deps()
       for pkg in pkgs:
            out = os.popen("dpkg -l | grep -F '" + pkg + "'").read()
            assert out is not ''

    @pytest.mark.skip(reason="New hire will work on this")
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
        


    @pytest.mark.skip(reason="New hire will work on this")
    def test_install_bgpdump(self):
        """Tests installation of bgpdump and dependencies

        First uninstall all dependencies listed.
        Then install all of them
        no files should be leftover
        Should be able to be called twice and not error
        Should test bgpdump to ensure it doesn't error
            -potentially borrow test from test_mrt_file for this

        """

        installer = MRT_Installer()
        filetest = Test_MRT_File()
        cmds = ["sudo rm -r -f /usr/bin/bgpdump", 
                "sudo rm -r -f /usr/local/bin/bgpdump"]
        installer._install_bgpdump()
        filetest.test_bgpdump_regex()

