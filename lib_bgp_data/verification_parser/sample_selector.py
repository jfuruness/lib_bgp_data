#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class sample_selector

See github
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from .tables import Collectors_Table
from .tables import Top_100_Collectors_Table
from .tables import Top_100_w_100k_Prefixes_Table


class Sample_Selector:
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def select_samples(self):
        # Step 1:
        # Get a table of all collectors
        self._get_collectors_table()
        # Step 2:
        # Order collectors by AS rank, get only top 100 out of that
        self._get_top_100_collectors_table()
        # Step 3:
        # Filter further by only collectors that have over 100k prefixes
        self._get_top_collectors_w_100k_prefix_origins_table()
        # Step 4:
        # select distinct by prefix, path, and origin announcements
        # For these collectors
        self._get_top_collectors_w_100k_prefix_origins_with_distinct_table()
        # Step 5:
        # Filter by only collectors that have, for each prefix, 1 origin and 1 path
        self._get_top_collectors_w_100k_prefix_origins_with_distinct_table()
        # Step 6:
        # Filter mrt announcements even further by this
        # Get control mrt ann - ann that originate at a collector
        self._get_control_mrt_ann()
        # Step 7:
        # Assert that you have enough collectors and announcements
        assert False, """Make sure you have enough collectors by this point, as an assert
                        do this in prev fun. Also assert for announcements"""
        # Step 8:
        # Select top X collectors and randomly select Xk announcements
        self.get_final_set_of_collectors_and_control_ann()
        # Step 9:
        # Get test mrt ann - ann that overlap with the control mrt anm
        # Note that this includes control mrt ann
        self._get_test_mrt_ann()

        # Note that announcements are announcements with same prefix
        # Note that these announcements come from full set of mrts,
        # Not just the ones we are going to use for control set w/collectors
        # NOTE also that these ann must be distinct by prefix as_path origin!!

    def _get_collectors_table(self):
        """Returns table of collectors

        collectors are the last in the as path, since they are
        write before the collector itself
        """

        with Collectors_Table(clear=True) as db:
            db.fill_table()

    def _get_top_100_collectors_table(self):
        """Get top 100 collectors by as rank"""

        with Top_100_Collectors_Table(clear=True) as db:
            db.fill_table()

    def _get_top_collectors_w_100k_prefixes(self):
        """Gets all collectors in...

        top 100 ases by as rank that have over 100k prefix origin pairs
        """

        with Top_100_w_100k_Prefixes_Table(clear=True) as db:
            db.fill_table()

    def _get_top_collectors_w_100k_prefix_origins_with_distinct_table(self):
        """Gets only the good collectors (for testing) that have...

        for each prefix, one origin and path
        """

        assert False, "Impliment, potentially add to last func?? check all tables here"

    def _get_potential_control_mrt_ann(self):
        """Get only mrt announcements that have a good collector

        Makes sure that they are distinct"""

        assert False, "Impliment"

    def get_final_set_of_collectors_and_control_ann(self):
        """Selects X collectors and X good announcements from

        good collectors and potential control announcements
        """

        assert False, "impliment"

    def _get_test_mrt_ann(self):
        """Gets mrt ann that overlap with control ann from a good collector

        makes sure that they are distinct
        """

        assert False, "Impliment"
