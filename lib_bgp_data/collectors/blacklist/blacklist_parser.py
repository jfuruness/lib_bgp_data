#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist parser

The purpose of this class is to download a list of blacklisted ASNs
from UCEPROTECT's level 2 and 3 blacklists, Spamhaus's ASN blacklist,
and the results from a MIT paper, and insert them into a database.
For more information on sources, please see the readme
"""
__authors__ = ["Nicholas Shpetner", "Justin Furuness"]
__credits__ = ["Nicholas Shpetner", "Justin Furuness"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

from .blacklist_sources import UCE_Blacklist, UCE_Blacklist_IP
from .blacklist_sources import UCE1, UCE2, UCE2_IP, UCE3, UCE3_IP
from .blacklist_sources import Spamhaus_asndrop, Spamhaus_drop 
from .blacklist_sources import Spamhaus_edrop, MIT_Blacklist
from .blacklist_source import Blacklist_Source
from .tables import Blacklist_Table
from ...utils.base_classes import Parser
from ...utils import utils

class Blacklist_Parser(Parser):

    __slots__ = []

    def _run(self):

        rows = []
        for Source in Blacklist_Source.sources:
            rows.extend(Source(self.csv_dir).run())

        utils.rows_to_db(rows, f"{self.csv_dir}/blist.csv", Blacklist_Table)
