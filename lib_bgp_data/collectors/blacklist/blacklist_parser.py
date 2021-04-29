#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist parser.

The purpose of this module is to download a list of blacklisted ASNs
and IPs from UCEPROTECT's blacklists, Spamhaus's blacklists,
and the results from a MIT paper, and insert them into a table.
For more information on sources, see sources.txt, located in this dir

The table, blacklist, is made up of three columns:
    - asn: The ASN of a blacklisted AS in the format ######
    - prefix: the IP of a blacklisted IP or range in IPv4 or CIDR
    - source: which blacklist the asn/prefix came from
Either asn or prefix will be left blank with a value of None depending
on if the blacklisted item was a asn or prefix, in which the other
identifier will be set to None. 


There are no known cavaets or issues with rate limits and the like
over the course of normal usage with the sources given.

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
