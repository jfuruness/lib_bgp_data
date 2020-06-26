#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the Hurricane Website Parser

The purpose of this class is to parse the information on bgp.he.net using
hijacks table. For each row in the hijacks table, the website will be queried
with the row's prefixes. If it is a prefix attack, then the website will only
need to be queried once. If it is a subprefix attack, then both the prefix and
the subprefix will need to be queried. This will be done for each row in the
hijacks table. The information parsed from the bgp.he.net website will be
inserted into a table named hurrican_as.
"""

__author__ = "Samarth Kasbawala"
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .hurricane_website_parser import Hurricane_Website_Parser

