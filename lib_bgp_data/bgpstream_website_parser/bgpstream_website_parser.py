#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class BGPStream_Website_Parser
The BGPStream_Website_Parser inserts bgpstream.com into the db
The parser is not multithreaded because the website eventually blocks you
"""

import re
import requests
import shutil
import os
import bs4
from enum import Enum
from ..utils import error_catcher, utils
from .data_classes import Leak, Hijack, Outage 

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Event_Types(Enum):
    """Possible bgpstream.com event types"""

    HIJACK = "Possible Hijack"
    LEAK = "BGP Leak"
    OUTAGE = "Outage"

class BGPStream_Website_Parser:
    """This class inserts information from bgpstream.com into the db"""

    __slots__ = ['path', 'csv_dir', 'args', 'logger', 'config', 'data',
                 'all_files', 'data_types']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Inits paths, args, logger, config, etc
        utils.set_common_init_args(self, args)
        self.data = {Event_Types.HIJACK.value: Hijack(self.logger,
                                                      self.csv_dir),
                     Event_Types.LEAK.value: Leak(self.logger,
                                                  self.csv_dir),
                     Event_Types.OUTAGE.value: Outage(self.logger,
                                                      self.csv_dir)}

    @error_catcher()
    @utils.run_parser()
    def parse(self, start, end, row_limit=None, db=True, IPV4=True, IPV6=False,
              data_types=[Event_Types.HIJACK.value]):
        """Parses rows in the bgpstream website

        Row limit is for testing purposes only, to run a small subset. The
        possible values for data_types are anything in the Event_Types"""


        self.data_types = data_types
        rows, _ = utils.get_tags("https://bgpstream.com", "tr")
        # We do this because the last few rows are screwed up
        rows = rows[:-10]
        # The last couple of rows are corrupted, so reduce rows parsed
        if row_limit is None or row_limit > len(rows):
            row_limit = len(rows)

        # Parses all rows
        for i, row in enumerate(rows):
            if i > row_limit: break
            self._parse_row(row, i, len(rows))

        # Writes to csvs and dbs and deletes duplicates and creates indexes
        # And also creates the temporary tables
        [self.data[x].db_insert(start, end, IPV4, IPV6) for x in data_types]

    @error_catcher()
    def _parse_row(self, row, num, total):
        """Parses a row"""

        self.logger.info("Parsing row {}/{}".format(num, total))
        _type = [x for x in row.children][1].string.strip()
        # If the event_type is in the list of types we are parsing
        if _type in self.data_types:
            # Append the parsed info to the row
            self.data[_type].append(row)
