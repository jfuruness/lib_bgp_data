#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains all of the data classes for parsing

The purpose of these classes is to parse information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. Please note that each data class inherits from the
Data class. For each data class, This is done through a series of steps.

1. Initialize the class
    -Handled in the __init__ function
    -Sets the table and the csv_path, and then calls __init__ on Data
2. Call __init__ on the parent class Data.
    -This initializes all regexes
    -The data list of all events of that type is also initialized
3. Rows are appended to each data class
    -This is handled by the BGPStream_Website_Parser class
    -The append function is overwritten in the parent Data class
4. For each row, parse the common elements
    -Handled by the append _parse_common_elements in the Data class
    -Gets all information that is generic to all events
5. Pass extra information to the _parse_uncommon_elements function
    -This is a function specified by each subclass
    -This function parses elements that are specific to that event type
6. Then the row is formatted for csv insertion and appended to self.data
    -Formatting is handled by the _format_temp_row() in the Data Class
7. Later the BGPStream_Website_Parser will call the db_insert function
    -This is handled in the parent Data class
    -This will insert all rows into a CSV
        -This is done because CSVs have fast bulk insertion time
    -The CSV will then be copied into the database
8. After the data is in the database, the tables will be formatted
    -First the tables remove unwanted IPV4 and IPV6 values
    -Then an index is created if it doesn't exist
    -Then duplicates are deleted if they exist
    -Then temporary tables are created
        -These are tables that are subsets of the overall data

Design Choices (summarizing from above):
    -A parent data class is used because many functions are the same
     for all data types
    -This is a mess, parsing this website is messy so I will leave it
    -Parsing is done from the last element to the first element
        -This is done because not all pages start the same way

Possible Future Extensions:
    -Add test cases
    -Ask bgpstream.com for an api?
        -It would cause less querying of their site
"""


import re
from ..utils import utils, error_catcher, db_connection
from .tables import Hijack_Table, Outage_Table, Leak_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Data:
    """Parent Class for parsing rows of bgpstream.com.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = ['logger', '_as_regex', '_nums_regex', '_ip_regex',
                 '_temp_row', 'data', '_columns']

    @error_catcher()
    def __init__(self, logger):
        """Initializes regexes and other important info."""

        self.logger = logger
        self.logger.debug("Initialized row")
        # This regex parses out the AS number and name from a string of both
        self._as_regex = re.compile(r'''
                                    (?P<as_name>.+?)\s\(
                                    AS\s(?P<as_number>\d+)\)
                                    |
                                    (?P<as_number2>\d+).*?\((?P<as_name2>.+?)\)
                                    ''', re.VERBOSE
                                    )
        # This regex returns a string that starts and ends with numbers
        self._nums_regex = re.compile(r'(\d[^a-zA-Z\(\)\%]*\d*)')
        # This regex is used in some places to get prefixes
        self._ip_regex = re.compile(r'.+?:(.+)')
        # This is a list of parsed event information
        self.data = []
        # This gets the columns of the event type for the table
        with db_connection(self.table, self.logger) as t:
            self._columns = t.columns

    @error_catcher()
    def append(self, row):
        """Parses, formats, and appends a row of data from bgpstream.com.

        For a more in depth explanation see the top of the file."""

        # Initializes the temporary row
        self._temp_row = {}
        # Gets the common elements and stores them in temp_row
        # Gets the html of the page for that specific event
        as_info, extended_children = self._parse_common_elements(row)
        # Parses uncommon elements and stores them in temp_row
        self._parse_uncommon_info(as_info, extended_children)
        # Formats the temp_row and appends it to the list of events
        self.data.append(self._format_temp_row())

    @error_catcher()
    def db_insert(self, start, end, IPV4=True, IPV6=False):
        """Inserts the data into the database and formats it.

        Start and end should be in epoch. The data is inserted into the
        database, then undesired IPV types are removed, indexes are
        created, duplicates deleted, and subtables created. For a more
        in depth explanation see the top of the file.
        """

        # Inserts data into the database
        utils.rows_to_db(self.logger, self.data, self.csv_path, self.table,
                         clear_table=False)

        with db_connection(self.table, self.logger) as db_table:
            # Removes unwanted prefixes
            db_table.filter(IPV4, IPV6)
            # Creates indexes
            db_table.create_index()
            # Deletes duplicates in the table
            db_table.delete_duplicates()
            # Creates all subtables
            db_table.create_temp_table(start, end)


########################
### Helper Functions ###
########################

    @error_catcher()
    def _parse_common_elements(self, row):
        """Parses common tags and adds data to temp_row.

        All common elements on the initial page are parsed, then the
        html for the url for that event in that row is retrieved. For a
        more in depth explanation please see the top of the file.

        The first return value is the list of strings for as_info.
        The second return value is a list of more tags to parse.
        """

        children = [x for x in row.children]
        self._temp_row = {"event_type": children[1].string.strip()}
        # Must use stripped strings here because the text contains an image
        self._temp_row["country"] = " ".join(children[3].stripped_strings)
        try:
            # If there is just one string this will work
            as_info = children[5].string.strip()
        except:  # Should not use bare except
            # If there is more than one AS this will work
            stripped = children[5].stripped_strings
            as_info = [x for x in stripped]
        # Gets common elements
        self._temp_row["start_time"] = children[7].string.strip()
        self._temp_row["end_time"] = children[9].string.strip()
        self._temp_row["url"] = children[11].a["href"]
        self._temp_row["event_number"] = self._nums_regex.search(
            self._temp_row["url"]).group()
        url = 'https://bgpstream.com' + self._temp_row["url"]
        # Returns the as info and html for the page with more info
        return as_info, utils.get_tags(url, "td")[0]

    @error_catcher()
    def _parse_as_info(self, as_info):
        """Performs regex on as_info to return AS number and AS name.

        This is a mess, but that's because parsing html is a mess.
        """

        # Get group objects from a regex search
        as_parsed = self._as_regex.search(as_info)
        # If the as_info is "N/A" and the regex returns nothing
        if as_parsed is None:
            # Sometimes we can get this
            try:
                return None, re.findall(r'\d+', as_info)[0]
            # Sometimes not
            except:  # Should not use bare except
                return None, None
        else:
            # This is the first way the string can be formatted:
            if as_parsed.group("as_number") not in [None, "", " "]:
                return as_parsed.group("as_name"), as_parsed.group("as_number")
            # This is the second way the string can be formatted:
            elif as_parsed.group("as_number2") not in [None, "", " "]:
                return as_parsed.group("as_name2"),\
                    as_parsed.group("as_number2")

    @error_catcher()
    def _format_temp_row(self):
        """Formats row vals for input into the csv files.

        _id columns are excluded from the columns.
        """

        # Quotes need to be replaced because it screws up csv insertion
        # for like that one stupid AS that has a quote in it's name
        return_list = []
        for column in self._columns:
            val = self._temp_row.get(column)
            if val is not None:
                return_list.append(val.replace('"', ""))
            else:
                return_list.append(val)
        return return_list


class Hijack(Data):
    """Class for parsing Hijack events. Inherits from Data.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = ['table', 'csv_path']

    @error_catcher()
    def __init__(self, logger, csv_dir):
        """Initializes row instance and determine info about it.

        For a more in depth explanation see the top of the file."""

        self.table = Hijack_Table
        self.csv_path = "{}/hijack.csv".format(csv_dir)
        Data.__init__(self, logger)

    @error_catcher()
    def _parse_uncommon_info(self, as_info, extended_children):
        """Parses misc hijack row info."""

        self._temp_row["expected_origin_name"],\
            self._temp_row["expected_origin_number"]\
            = self._parse_as_info(as_info[1])
        self._temp_row["detected_origin_name"],\
            self._temp_row["detected_origin_number"]\
            = self._parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        self._temp_row["expected_prefix"] = self._ip_regex.search(
            extended_children[end - 6].string).group(1).strip()
        self._temp_row["more_specific_prefix"] = self._ip_regex.search(
            extended_children[end - 4].string).group(1).strip()
        self._temp_row["detected_as_path"] = self._nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        self._temp_row["detected_as_path"] = str([int(s) for s in
            self._temp_row.get("detected_as_path").split(' ')])
        self._temp_row["detected_as_path"] =\
            self._temp_row.get("detected_as_path"
                               ).replace('[', '{').replace(']', '}')
        self._temp_row["detected_by_bgpmon_peers"] = self._nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)
        self.logger.debug("Parsed Hijack Row")


class Leak(Data):
    """Class for parsing Leak events. Inherits from Data.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = ['table', 'csv_path']

    @error_catcher()
    def __init__(self, logger, csv_dir):
        """Initializes row instance and determine info about it.

        For a more in depth explanation see the top of the file."""

        self.table = Leak_Table
        self.csv_path = "{}/leak.csv".format(csv_dir)
        Data.__init__(self, logger)

    @error_catcher()
    def _parse_uncommon_info(self, as_info, extended_children):
        """Parses misc leak row info."""

        self._temp_row["origin_as_name"], self._temp_row["origin_as_number"] =\
            self._parse_as_info(as_info[1])
        self._temp_row["leaker_as_name"], self._temp_row["leaker_as_number"] =\
            self._parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        self._temp_row["leaked_prefix"] = self._nums_regex.search(
            extended_children[end - 5].string.strip()).group(1).rstrip()
        leaked_to_info = [x for x in
                          extended_children[end - 3].stripped_strings]
        # We use arrays here because there could be several AS's
        self._temp_row["leaked_to_number"] = []
        self._temp_row["leaked_to_name"] = []
        # We start the range at 1 because 0 returns the string: "leaked to:"
        for i in range(1, len(leaked_to_info)):
            name, number = self._parse_as_info(leaked_to_info[i])
            self._temp_row["leaked_to_number"].append(int(number))
            self._temp_row["leaked_to_name"].append(name)
        self._temp_row["leaked_to_number"] =\
            str(self._temp_row.get("leaked_to_number")
                ).replace('[', '{').replace(']', '}')
        self._temp_row["leaked_to_name"] =\
            str(self._temp_row.get("leaked_to_name")
                ).replace('[', '{').replace(']', '}')
        example_as_path = self._nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        example_as_path = str([int(s) for s in example_as_path.split(' ')])
        self._temp_row["example_as_path"] =\
            example_as_path.replace('[', '{').replace(']', '}')
        self._temp_row["detected_by_bgpmon_peers"] = self._nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)
        self.logger.debug("Parsed leak")


class Outage(Data):
    """Class for parsing outage events. Inherits from Data.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = ['table', 'csv_path']

    @error_catcher()
    def __init__(self, logger, csv_dir):
        """Initializes row instance and determine info about it.

        For a more in depth explanation see the top of the file."""

        self.table = Outage_Table
        self.csv_path = "{}/outage.csv".format(csv_dir)
        Data.__init__(self, logger)

    @error_catcher()
    def _parse_uncommon_info(self, as_info, extended_children):
        """Parses misc outage row info."""

        self._temp_row["as_name"], self._temp_row["as_number"] =\
            self._parse_as_info(as_info)
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        prefix_string = extended_children[
            len(extended_children) - 1].string.strip()
        # Finds all the numbers within a string
        prefix_info = self.nums_regex.findall(prefix_string)
        self._temp_row["number_prefixes_affected"] = prefix_info[0]
        self._temp_row["percent_prefixes_affected"] = prefix_info[1]
        self.logger.debug("Parsed Outage")
