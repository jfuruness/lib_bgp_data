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
import re

from .blacklist_source import *
from ...utils import utils

class UCE_Blacklist(Blacklist_Source):
    """Why am I using an IP for UCE's mirrors? The various mirrors
    of UCE's blacklists are not consistent with one another:
    Some will return a gzip, some just ISO-8859 text, and some
    just don't work. So, to ensure consistency, I'm using IP.
    This should return plaintext."""

    def download(self):
        temp_path = self.path + ".gz"
        utils.download_file(self.url, temp_path)
        utils.unzip_gz(temp_path)

class UCE_Blacklist_IP(Blacklist_Source_IP):
    def download(self):
        temp_path = self.path + ".gz"
        utils.download_file(self.url, temp_path)
        utils.unzip_gz(temp_path)
     
    def parse_file(self, f):
        return set(re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', f.read()))

class UCE_Blacklist_MULTI(Blacklist_Source):
    def download(self):
        temp_path = self.path + ".gz"
        utils.download_file(self.url, temp_path)
        utils.unzip_gz(temp_path)

    def parse_file(self, f):
        parsed = []
        for line in f:
            line_string = line
            cidr = re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,3}', line_string)
            if cidr is not None:
                cidr = cidr[0]
            asn = re.findall(r'AS(\d+)', line_string)
            if cidr is not None and asn is not None and asn != []:
                asn = asn.pop()
                parsed.append((asn, cidr))
        return parsed

    def get_rows(self, parsed):
        """Returns ASNs and CIDRs for db insertion"""
        return [[line[0], line[1], self.__class__.__name__] for line in parsed]

class UCE1(UCE_Blacklist_IP):
    url = 'http://41.208.71.58/rbldnsd-all/dnsbl-1.uceprotect.net.gz'

class UCE2(UCE_Blacklist_MULTI):
    url = 'http://72.13.86.154/rbldnsd-all/dnsbl-2.uceprotect.net.gz'

class UCE2_IP(UCE_Blacklist_IP): 
    url = 'http://72.13.86.154/rbldnsd-all/dnsbl-2.uceprotect.net.gz'

class UCE3(UCE_Blacklist_MULTI):
    url = 'http://72.13.86.154/rbldnsd-all/dnsbl-3.uceprotect.net.gz'

class UCE3_IP(UCE_Blacklist_IP):
    url = 'http://72.13.86.154/rbldnsd-all/dnsbl-3.uceprotect.net.gz'

class Spamhaus_asndrop(Blacklist_Source):
    url = 'https://www.spamhaus.org/drop/asndrop.txt'

class Spamhaus_drop(Blacklist_Source_CIDR):
    url = 'https://www.spamhaus.org/drop/drop.txt'

class Spamhaus_edrop(Blacklist_Source_CIDR):
    url = 'https://www.spamhaus.org/drop/edrop.txt'

class MIT_Blacklist(Blacklist_Source):
    url = ('https://raw.githubusercontent.com/ctestart/BGP-SerialHijackers/'
           'master/prediction_set_with_class.csv')

    def parse_file(self, f):
        reader = csv.DictReader(f, delimiter=',')
        # If HardVotePred is 1, MIT flagged ASN as serial hijacker
        return set(x['ASN'] for x in reader if x['HardVotePred'] == '1')
