#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class BGPStream_Website_Parser

The purpose of this class is to parse the information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. This is done through a series of steps.

1. Initialize the three different kinds of data classes.
    -Handled in the __init__ function
    -This class mainly deals with accessing the website, the data
     classes deal with parsing the information.
2. All rows are recieved from the main page of the website
    -This is handled in the utils.get_tags function
    -This has some initial data for all bgp events
3. The last ten rows on the website are removed
    -This is handled in the parse function
    -There is some html errors there, which causes errors when parsing
4. The row limit is set so that it is not too high
    -This is handled in the parse function
    -This is to prevent going over the maximum number of rows on website
5. Rows are iterated over until row_limit is reached
    -This is handled in the parse function
6. For each row, if that row is of a datatype passed in the parameters,
   and it is new data, add that to the self.data dictionary
    -A row is "new" if the start or end times are new or have changed
    -A paramater called refresh can be set to true to get all new rows
7. Call the db_insert funtion on each of the data classes in self.data
    -This will parse all rows and insert them into the database

Design Choices (summarizing from above):
    -The last ten rows of the website are not parsed due to html errors
    -Only the data types that are passed in as a parameter are parsed
        -In addition, only new rows (by default) are parsed
            -This is because querying each individual events page for
             info takes a long time
    -Multithreading isn't used because the website blocks the requests

Possible Future Extensions:
    -Only parse entries that have new or changed data
    -Add test cases
"""

from enum import Enum
from ..utils import error_catcher, utils, db_connection
from .tables import Hijack_Table, Leak_Table, Outage_Table
from .data_classes import Leak, Hijack, Outage

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Event_Types(Enum):
    """Possible bgpstream.com event types"""

    HIJACK = "Possible Hijack"
    LEAK = "BGP Leak"
    OUTAGE = "Outage"


class BGPStream_Website_Parser:
    """This class parses bgpstream.com information into a database.

    For a more in depth explanation, read the top of the file.
    """

    __slots__ = ['path', 'csv_dir', 'logger', '_data', '_data_types']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes path, csv_dir, logger, and data"""

        # Inits paths, csv_dir, logger
        utils.set_common_init_args(self, args)
        # These classes are used for parsing rows
        self._data = {Event_Types.HIJACK.value: Hijack(self.logger,
                                                       self.csv_dir),
                      Event_Types.LEAK.value: Leak(self.logger,
                                                   self.csv_dir),
                      Event_Types.OUTAGE.value: Outage(self.logger,
                                                       self.csv_dir)}

    @error_catcher()
    @utils.run_parser()
    def parse(self, start=None, end=None, row_limit=None, IPV4=True,
              IPV6=False, data_types=[Event_Types.HIJACK.value],
              refresh=False):
        """Parses rows in the bgpstream website.

        start and end should be epoch time. The temporary tables will be
        generated for these times. row_limit is for testing purposes
        only, to run a small subset. IPV4 and IPV6 are the prefixes that
        should be included if true. The possible values for data_types
        are anything in the Event_Types enum, these are the values that
        will be parsed, everything else will be ignored. By default
        refresh is false, meaning only new rows are parsed. If refresh
        is set to True then all rows with a type in data_types will be
        parsed.

        For a more in depth explanation, refer to the top of the file.
        """

        # The data types to parse, from the enum
        self._data_types = data_types
        # Gets the rows to parse
        rows, _ = utils.get_tags("https://bgpstream.com", "tr")
        # The last few rows are screwed up so they are removed
        rows = rows[:-10]
        # Reduce/set row_limit to total number of rows
        if row_limit is None or row_limit > len(rows):
            row_limit = len(rows)

        known_events = self._generate_known_events()

        self.logger.info("Beginning to parse rows")
        # Parses rows if they are the event types desired
        for i, row in enumerate(rows):
            # Make sure the row_limit is not reached
            # Should this be on two lines? Probably, I just didn't
            # even know you could do this, likely because it's so dumb
            if i > row_limit: break
            # Print every 250 rows
            print_me = True if i % 250 == 0 or i == row_limit - 1 else False
            # Parses the row
            self._parse_row(row, i, len(rows), known_events, refresh, print_me)

        # Writes to csvs and dbs, deletes duplicatesm and creates indexes
        # Also creates the temporary tables
        [self._data[x].db_insert(start, end, IPV4, IPV6) for x in data_types]

    @error_catcher()
    def _parse_row(self, row, num, total, known_events, refresh, print_me):
        """Parses all rows that fit certain requirements.

        Each row must have a type withing self.data_types.
        Each row must be new, and have a different start/end
        or refresh must be set to true.
        """

        self.logger.debug("Starting to parse row {}/{}".format(num, total))
        # Gets the type of event (in the events enum) for the row
        _type = [x for x in row.children][1].string.strip()

        start = [x for x in row.children][7].string.strip() + '+00:00'
        end = [x for x in row.children][9].string.strip() + '+00:00'
        url = [x for x in row.children][11].a["href"]
        event_num = url.split("/")[-1]
        if end == "+00:00":
            end = 'None'

        if print_me:
            self.logger.info("Parsed {}/{} rows".format(num, total))

        # If the event_type is in the list of types we are parsing
        # If we've seen the event before, and the start and end haven't changed
        # then ignore the event entirely
        if _type in self._data_types:
            # Can't fit all on one line whatevs man idc
            if known_events.get(int(event_num)) != (start, end) or refresh:
                # Note that the append method is overriden
                # This will parse the row and then append the parsed
                # information in a list inside self.data[_type]
                self.logger.debug("Parsing row {}/{}".format(num, total))
                self._data[_type].append(row)

    @error_catcher()
    def _generate_known_events(self):
        """Generates known events.

        This could be done in a single sql query, but this makes sure
        the tables are generated first. The returned dict has the keys
        as the event_number of the table, and the tuple of (start, end)
        as the value, where start and end are strings in utc.
        """

        events = {}
        # Gets known events from hijack table
        with db_connection(Hijack_Table, self.logger) as h_table:
            sql = "SELECT start_time, end_time, event_number FROM hijack"
            for x in h_table.execute(sql):
                events[x["event_number"]] = (str(x["start_time"]),
                                             str(x["end_time"]))

        # Gets known events from the leak table
        with db_connection(Leak_Table, self.logger) as l_table:
            sql = "SELECT start_time, end_time, event_number FROM leak"
            for x in l_table.execute(sql):
                events[x["event_number"]] = (str(x["start_time"]),
                                             str(x["end_time"]))

        # Gets known events from the outage table
        with db_connection(Outage_Table, self.logger) as o_table:
            sql = "SELECT start_time, end_time, event_number FROM outage"
            for x in o_table.execute(sql):
                events[x["event_number"]] = (str(x["start_time"]),
                                             str(x["end_time"]))

        return events
