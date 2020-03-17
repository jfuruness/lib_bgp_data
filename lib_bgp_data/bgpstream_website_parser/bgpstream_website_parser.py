#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class BGPStream_Website_Parser

The purpose of this class is to parse the information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. See README for more in depth details.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

import bs4
from tqdm import tqdm

from .data_classes import Leak, Hijack, Outage
from .event_types import Event_Types
from .tables import Hijacks_Table, Leaks_Table, Outages_Table
from ..base_classes import Parser
from ..utils import utils


class BGPStream_Website_Parser(Parser):
    """This class parses bgpstream.com information into a database.

    For a more in depth explanation, read the top of the file.
    """

    __slots__ = ['_data']

    
    def _run(self,
             row_limit: int = None,
             IPV4=True,
             IPV6=False,
             data_types: list = Event_Types.list_values(),
             refresh=False):
        """Parses rows in the bgpstream website.

        row_limit is for testing purposes only, to run a small subset.
        IPV4 and IPV6 are the prefixes that should be included if true.
        The possible values for data_types are anything in Event_Types,
        these are the values that will be parsed, everything else will
        be ignored. By default refresh is false, meaning only new rows
        are parsed. If refresh is set to True then all rows with a type
        in data_types will be parsed.

        For a more in depth explanation, refer to README.
        """

        # These classes are used for parsing rows
        _data = {Event_Types.HIJACK.value: Hijack(self.csv_dir),
                 Event_Types.LEAK.value: Leak(self.csv_dir),
                 Event_Types.OUTAGE.value: Outage(self.csv_dir)}
        self._data = {k: v for k, v in _data.items()
                      if k in data_types}

        known_events = self._generate_known_events()

        # Parses rows if they are the event types desired
        rows: list = self._get_rows(row_limit)
        tqdm_desc = f"Parsing {' and '.join(self._data.keys())}"
        for row in tqdm(rows, desc=tqdm_desc, total=len(rows)):
            # Parses the row
            self._parse_row(row, known_events, refresh)

        # Writes to csvs and dbs, deletes duplicatesm and creates indexes
        # Also creates the temporary tables
        for x in self._data.values():
            x.db_insert(IPV4, IPV6)

    def _get_rows(self, row_limit: int):
        """Returns rows within row limit"""

        # Gets the rows to parse
        rows = utils.get_tags("https://bgpstream.com", "tr")
        # Reduce/set row_limit to total number of rows
        # We remove last ten rows because html is messed up
        if row_limit is None or row_limit > len(rows) - 10:
            row_limit = len(rows)

        return rows[:row_limit]

    def _parse_row(self,
                   row: bs4.element.Tag,
                   known_events: dict,
                   refresh: bool):
        """Parses all rows that fit certain requirements.

        Each row must have a type withing self.data_types.
        Each row must be new, and have a different start/end
        or refresh must be set to true.
        """

        _type, start, end, url, event_num = self._get_row_front_page_info(row)

        # If the event_type is in the list of types we are parsing
        # If we've seen the event before, and the start and end haven't changed
        # then ignore the event entirely
        if _type in self._data:
            # Can't fit all on one line whatevs man idc
            if known_events.get(int(event_num)) != (start, end) or refresh:
                # Note that the append method is overriden
                # This will parse the row and then append the parsed
                # information in a list inside self.data[_type]
                self._data[_type].append(row)
                logging.debug("Appending")

    def _get_row_front_page_info(self, row: bs4.element.Tag) -> tuple:
        """Returns type of event, start, end, url, event num.

        Essentially, all info available on front page of bgpstream.com.
        """

        # Gets the type of event (in the events enum) for the row
        _type: str = [x for x in row.children][1].string.strip()

        start: str = [x for x in row.children][7].string.strip() + '+00:00'
        end: str = [x for x in row.children][9].string.strip() + '+00:00'
        url: str = [x for x in row.children][11].a["href"]
        event_num: str = url.split("/")[-1]
        if end == "+00:00":
            end = 'None'

        return _type, start, end, url, event_num
    
    def _generate_known_events(self) -> dict:
        """Generates known events.

        This could be done in a single sql query, but this makes sure
        the tables are generated first. The returned dict has the keys
        as the event_number of the table, and the tuple of (start, end)
        as the value, where start and end are strings in utc.
        """

        events = {}
        for _Table_Class in [Hijacks_Table, Leaks_Table, Outages_Table]:
            # Gets known events from table
            with _Table_Class() as _db:
                sql = f"""SELECT start_time, end_time, event_number
                      FROM {_Table_Class.name}"""
                for x in _db.execute(sql):
                    events[x["event_number"]] = (str(x["start_time"]),
                                                 str(x["end_time"]))

        return events
