#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist source

this contains the base class for all blacklists.

The base class handles initalization, downloading, and parsing of
data from backlists.

The base class will parse for ASNs. Blacklist_Source_IP checks for IPv4
"""

__authors__ = ["Nicholas Shpetner", "Justin Furuness"]
__credits__ = ["Nicholas Shpetner", "Justin Furuness"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import re
import os

from ...utils import utils

class Blacklist_Source:

    sources = []
    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses
        This is incredibly useful for a few reasons. Mainly, you can
        strictly enforce proper templating with this. And also, you can
        automatically add all of these things to things like argparse
        calls and such. Very powerful tool.
        This assumes the sources uses ASNs.
        """

        super().__init_subclass__(**kwargs)
        if hasattr(cls, "url"):
            cls.sources.append(cls)

    def __init__(self, csv_dir):
        self.csv_dir = csv_dir

    def run(self):
        self.download()
        return self.get_rows(self.parse())

    def download(self):
        utils.download_file(self.url, self.path)

    @property
    def path(self):
        return os.path.join(self.csv_dir, self.__class__.__name__)

    def parse(self):
        with open(self.path, 'r', encoding="utf-8", errors="ignore") as f:
            return self.parse_file(f)

    def parse_file(self, f):
        "This parses for ASNs"
        return set(re.findall(r'AS(\d+)', f.read()))

    def get_rows(self, asns):
        """Returns rows for db insertion"""

        return [[asn, None, self.__class__.__name__] for asn in asns]

class Blacklist_Source_IP(Blacklist_Source):
    """This subclass of Blacklist_Source is made to handle blacklists
    that use IP instead of ASNs
    """
    def __init__(self, csv_dir):
        super().__init__(csv_dir)

    def parse_file(self, f):
        return set(re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', f.read()))

    def get_rows(self, prefix):
        """Returns prefixes for db insertion"""
        return [[None, pre, self.__class__.__name__] for pre in prefix]


class Blacklist_Source_CIDR(Blacklist_Source_IP):
    """This subclass of Blacklist_Source is made to handle blacklists
    that use CIDR with a mask at the end instead of just IPv4
    """
    def parse_file(self, f):
        return set(re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,3}', f.read()))
