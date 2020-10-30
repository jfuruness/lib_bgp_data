#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist sources

these inherit from the blacklist_source base class
"""

__authors__ = ["Nicholas Shpetner", "Justin Furuness"]
__credits__ = ["Nicholas Shpetner", "Justin Furuness"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import csv

from .blacklist_source import Blacklist_Source
from ..utils import utils

class UCE_Blacklist(Blacklist_Source):
    # Why am I using an IP for UCE's mirrors? The various mirrors
    # of UCE's blacklists are not consistent with one another:
    # Some will return a gzip, some just ISO-8859 text, and some
    # just don't work. So, to ensure consistency, I'm using IP.
    # This should return plaintext.

    def download(self):
        temp_path = self.path + ".gz"
        utils.download_file(self.url, temp_path)
        utils.unzip_gz(temp_path)

class UCE2(UCE_Blacklist):
    url = 'http://72.13.86.154/rbldnsd-all/dnsbl-2.uceprotect.net.gz'

class UCE3(UCE_Blacklist):
    url = 'http://72.13.86.154/rbldnsd-all/dnsbl-3.uceprotect.net.gz'

class Spamhaus_Blacklist(Blacklist_Source):
    url = 'https://www.spamhaus.org/drop/asndrop.txt'

class MIT_Blacklist(Blacklist_Source):
    url = ('https://raw.githubusercontent.com/ctestart/BGP-SerialHijackers/'
           'master/prediction_set_with_class.csv')

    def parse_file(self, f):
        reader = csv.DictReader(f, delimiter=',')
        # If HardVotePred is 1, MIT flagged ASN as serial hijacker
        return set(x['ASN'] for x in reader if x['HardVotePred'] == '1')
