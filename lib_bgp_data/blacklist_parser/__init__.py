#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist parser

The purpose of this class is to download a list of blacklisted/malicious ASNs from Spamhaus, UCEPROTECT, and a MIT paper, and insert them into a database.
"""

__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

from .blacklist_parser import Blacklist_Parser
