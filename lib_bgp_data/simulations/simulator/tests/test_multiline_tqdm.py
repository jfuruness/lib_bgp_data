#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the multiline_tqdm.py file.

For speciifics on each test, see the docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..multiline_tqdm import Multiline_TQDM


@pytest.mark.skip(reason="undergrad work")
@pytest.mark.simulator
class Test_Multiline_TQDM:
    """Tests all functions within the multiline tqdm class."""

    def test___init___and_close(self):
        """Tests initialization of the Multiline TQDM

        NOTE: please close it after completion
        """

        pass

    def test_context_manager(self):
        """Tests using the multiline tqdm as a context manager"""

        pass

    def test_update(self):
        """Tests calling the update func in multiline tqdm.

        make sure that the tqdm bars are all incrimented.
        """

        pass

    def test_update_extrapolator(self):
        """Tests calling the update extrapolator func.

        make sure that extrapolator running is changed to false.
        """

        pass

    def test_set_desc(self):
        """Tests the set_desc function.

        Parametize this, test with exr running and not
        make sure all text updates properly
        """

        pass

    def test_get_desc(self):
        """Tests the _get_desc function

        Make sure text is returned properly, both for None and real vals
        """

        pass
