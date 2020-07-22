#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..file import File


@pytest.mark.base_classes
class Test_File:
    """Tests the functions within the File class"""

    @pytest.mark.skip(reason="new hires work")
    def test_init(self):
        """Tests the init func of the file

        Make sure path is what you expect.
        """

    @pytest.mark.skip(reason="new hire work")
    def test_lt(self):
        """Tests the comparator operator for sorting"""

        pass
