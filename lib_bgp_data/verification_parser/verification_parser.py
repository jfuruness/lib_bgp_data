#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class verification_parser

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
The purpose of this is to generate input from 3 MRT file sources.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from .tables import Collectors_Table

from ..asrank_website_parser import ASRankWebsiteParser
from ..base_classes import Parser
from ..mrt_parser import MRT_Parser, MRT_Sources
from ..mrt_parser.tables import MRT_Announcements_Table

class Verification_Parser(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def _run(self,
             test=False,
             clear_db=False,
             mrt_announcements=Falseb,
             as_rank=False,
             sample_selection=False,
             ):
        if clear_db and not test:
            assert False, "Clear db, checkpoint, vaccum analyze"
        if mrt_announcements:
            kwargs = {"sources": [MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS],
                      "IPV4": True,
                      "IPV6": False}
            if test:
                kwargs["api_param_mods"] = {"collectors[]": ["route-views2",
                                                             "rrc03"]}
            MRT_Parser(**self.kwargs).run(**kwargs)
        if as_rank:
            ASRankWebsiteParser(**self.kwargs).run()
        if sample_selection:
            assert False, "Move this into Sample_Selector and import it"
            self.select_samples()


    def select_samples(self):
        assert False, "impliment this"
        ### LATER MUST MOVE THIS INTO ANOTHER class!!!
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

        assert False, "Impliment"
        with Top_100_Collectors_Table(clear=True) as db:
            db.fill_table()

    def _get_top_collectors_w_100k_prefix_origins_table(self):
        """Gets all collectors in...

        top 100 ases by as rank that have over 100k prefix origin pairs
        """

        assert False, "Impliment"

    def _get_top_collectors_w_100k_prefix_origins_with_distinct_table(self):
        """Gets only the good collectors (for testing) that have...

        for each prefix, one origin and path
        """

        assert False, "Impliment"

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
