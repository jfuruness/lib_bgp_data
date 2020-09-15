#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist source

this contains the base class for all blacklists
"""

__authors__ = ["Nicholas Shpetner", "Justin Furuness"]
__credits__ = ["Nicholas Shpetner", "Justin Furuness"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import re

from ..utils import utils

class Blacklist_Source:

    sources = []
    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses
        This is incredibly useful for a few reasons. Mainly, you can
        strictly enforce proper templating with this. And also, you can
        automatically add all of these things to things like argparse
        calls and such. Very powerful tool.
        """

        super().__init_subclass__(**kwargs)
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
        with open(self.path, 'r') as f:
            return self.parse_file(f)

    def parse_file(self, f):
        return set(re.findall(r'AS(\d+)', f.read()))

    def get_rows(self, asns):
        """Returns rows for db insertion"""

        return [[self.__class__.__name__, asn] for asn in asns]
