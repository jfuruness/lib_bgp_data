#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Hijack_End_Time_Parser

The purpose of this class is to download the end times for hijack events
into a database. This is done through a series of steps.

Read README for in depth explanation.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from datetime import datetime, timedelta
import logging
import os
from subprocess import check_output, DEVNULL

from ..base_classes import Parser
from ..bgpstream_website_parser.tables import Hijacks_Table
from ..utils import utils


class Hijack_End_Time_Parser(Parser):
    """This class downloads, parses, and deletes files from Caida.

    In depth explanation at the top of module.
    """

    def __init__(self, **kwargs):
        """Initializes logger and path variables."""

        super(Hijack_End_Time_Parser, self).__init__(**kwargs)
        if not os.path.exists("/usr/bin/bgpreader"):
            logging.warning("Dependencies are not installed. Installing now.")
            self._install_dependencies()

    def _run(self, *args):
        """doc later"""

        with Hijacks_Table() as db:
            hijacks = [Hijack(x) for x in db.get_all()]
        for hijack in hijacks[:1]:
            hijack.search_end_times()

    def _install_dependencies(self):
        pass

class Hijack:
    """Simple class to make hijacks easier to work with"""

    def __init__(self, row):
        self.start_time = row["start_time"]
        self.victim_prefix = row["expected_prefix"]
        self.attacker_prefix = row["more_specific_prefix"]
        self.victim_origin = row["expected_origin_number"]
        self.attacker_origin = row["detected_origin_number"]
        # Just in case
        self.row = row

    def search_end_times(self):
        end_time = self.start_time + timedelta(days=1)
        self.victim_end_time = self.search_end_time(self.victim_prefix,
                                                    self.victim_origin,
                                                    self.start_time.timestamp(),
                                                    end_time.timestamp())
        self.attacker_end_time = self.search_end_time(self.attacker_prefix,
                                                      self.attacker_origin,
                                                      self.start_time.timestamp(),
                                                      end_time.timestamp())
                                                    

    def search_end_time(self, prefix, origin_asn, time_1, time_2, record_type="ribs"):
        bash_args = ["bgpreader",
                     f"--time-window {int(time_1)},{int(time_2)}",
                     f"--prefix {prefix}",
                     f"--origin-asn {origin_asn}",
                     f"-t {record_type}"]

        output = check_output(" ".join(bash_args),
                              stderr=DEVNULL,
                              shell=True)
        from pprint import pprint
        pprint(output.split("\n"))
 
