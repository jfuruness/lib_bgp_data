#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the parser.py file.
For specifics on each test, see the docstrings under each function.
"""


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

from ..parser import Parser


@pytest.mark.base_classes
class Test_Parser:
    """Tests all functions within the Parser class."""

    @pytest.mark.skip(reason="New hire work")
    def test_init_subclass(self):
        """Test the __init_sublcass method.

        Make sure that all inherited classes are in the parsers list.
        """

    @pytest.mark.skip(reason="New hire work")
    def test__innit__(self):
        """Tests init function.

        Should have a section.
        Logging should be configured.
        path and csv directories should be created and empty
        should fail if _run not present, and vice versa.
        """

    @pytest.mark.skip(reason="New hire work")
    def test_run(self):
        """Tests the run function

        One test where there is an exception - do not raise, but log
            -test should still clean out dirs
        One test should be where there is no exception
            -tests should still clean out dirs
        """

    @pytest.mark.skip(reason="New hire work")
    def test_end_parser(self):
        """tests end_parser func

        Make's sure that dirs are cleaned out. Don't worry about the time.
        """

    @pytest.mark.skip(reason="New hire work")
    def test_argparse_call(self):
        """Tests argparse call method.

        See how __main__.py uses this function. Read the docstrings.
        Attempt to have a class be able to be called with this. Make
        sure that it works.
        """

        pass
