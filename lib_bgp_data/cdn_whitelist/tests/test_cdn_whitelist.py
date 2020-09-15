#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the cdn_whitelist.py file.

For speciifics on each test, see the docstrings under each function.
Note that we do NOT test the parse_roas function, because this is
essentially a database operation and is checked in another file
"""

__authors__ = ["Justin Furuness", "Tony Zheng"]
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from os import path

from ..cdn_whitelist import CDN_Whitelist
from ..tables import CDN_Whitelist_Table
from ...utils import utils

@pytest.mark.cdn_whitelist
class Test_CDN_Whitelist:
    """Tests all functions within the ROAs Parser class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Parser setup and table deleted before every test"""
        with CDN_Whitelist_Table(clear=True) as t:
            pass

    def test_run(self):
        """Tests the _run function"""

        # Downloads data and inserts into the database (should be more than 0 entries)
        # Makes sure it doesn't error even if there is a CDN that doesn't exist

        # Add a nonsense CDN
        list_path = path.dirname(path.dirname(path.realpath(__file__)))
        list_path = path.join(list_path, 'cdns.txt')
        utils.run_cmds(f'echo "urfgurf" >> {list_path}')

        CDN_Whitelist()._run()

        with CDN_Whitelist_Table() as t:
            assert t.get_count() > 0

        # Delete what was added
        utils.run_cmds(f"sed -i '$d' {list_path}")

        
