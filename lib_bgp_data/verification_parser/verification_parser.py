#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class verification_parser

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
The purpose of this is to generate input from 3 MRT file sources.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from ..asrank_website_parser import ASRankWebsiteParser
from ..base_classes import Parsre
from ..mrt_parser import MRT_Parser

class Verification_Parser(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def run(self,
            clear_db=False,
            mrt_annoucements=False,
            as_rank=False,
            sample_selection=False):
        if clear_db:
            assert False, "Clear db, checkpoint, vaccum analyze"
        if mrt_announcements:
            MRT_Parser(**self.kwargs).run(IPV4=True, IPV6=False)
        if as_rank:
            ASRankWebsiteParser(**self.kwargs).run()
        if sample_selection:
            ### LATER MUST MOVE THIS INTO ANOTHER class!!!
            # Step 1:
            # Get a table of all collectors
            # Step 2:
            # Order collectors by AS rank, get only top 100 out of that
            # Step 3:
            # Filter further by only collectors that have over 100k prefixes
            # Step 4:
            # select distinct by prefix, path, and origin announcements
            # For these collectors
            # Step 5:
            # Filter by only collectors that have, for each prefix, 1 origin and 1 path
            # Step 6:
            # Filter mrt announcements even further by this
            # Step 7:
            # Assert that you have enough collectors and announcements
            # Step 8:
            # Select top X collectors and randomly select Xk announcements
            # Note that announcements are announcements with same prefix
            # Note that these announcements come from full set of mrts,
            # Not just the ones we are going to use for control set w/collectors
            # NOTE also that these ann must be distinct by prefix as_path origin!!
            assert False, "Steps listed as comments above"
