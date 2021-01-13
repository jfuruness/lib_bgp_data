#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the mrt_installer.py file.

For speciifics on each test, see the docstrings under each function.
Note that if tests are failing, the self.start and self.end may need
updating to be more recent. Possibly same with the api_param_mods.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

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

        pass

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

        pass

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

        pass

