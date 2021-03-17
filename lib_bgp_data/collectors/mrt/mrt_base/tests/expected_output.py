#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains some strings for use in tests for mrt_file.
Not much else to say, other than that it works.
"""

__authors__ = ["Nicholas Shpetner"]
__credits__ = ["Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"


class Expected_Output:
    def __init__(self):
        # bgpscanner
        self.scanner = "=|1.2.3.0/24|12345 6789 0123 12345 67890|12.34.56.78|i|||1234:1 1234:2 1234:3 1234:4 5678:1 5678:2 5678:3 5678:4 5678:5|12.34.56.78|1234567890|1"
        # bgpdump
        self.dump = "TABLE_DUMP1|1234567890|B|1.2.3.4|12345|12.34.56.0/24|12345 67890 1234 5678 90|IGP"

    def get_scanner(self):
        return self.scanner

    def get_dump(self):
        return self.dump
