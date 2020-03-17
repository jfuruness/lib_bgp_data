#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains all of the data classes for parsing

The purpose of these classes is to parse information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. Please note that each data class inherits from the
Data class. For each data class, see README for in depth anything lol.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging
import re

import bs4

from .tables import Hijacks_Table, Outages_Table, Leaks_Table
from ..utils import utils


class Data:
    """Parent Class for parsing rows of bgpstream.com.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = ['_as_regex', '_nums_regex', '_ip_regex',
                 '_temp_row', 'data', '_columns', 'csv_path']

    
    def __init__(self, csv_dir: str):
        """Initializes regexes and other important info."""

        logging.debug("Initialized row")
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

        self.csv_path = f"{csv_dir}/{self.__class__.__name__.lower()}.csv"

        # This gets the columns of the event type for the table
        with self.table() as t:
            self._columns = t.columns

    
    def append(self, row: bs4.element.Tag):
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

    
    def db_insert(self, IPV4=True, IPV6=False):
        """Inserts the data into the database and formats it.

        Start and end should be in epoch. The data is inserted into the
        database, then undesired IPV types are removed, indexes are
        created, duplicates deleted, and subtables created. For a more
        in depth explanation see the top of the file.
        """

        # Inserts data into the database
        utils.rows_to_db(self.data, self.csv_path, self.table,
                         clear_table=False)

        with self.table() as db_table:
            # Removes unwanted prefixes
            if hasattr(db_table, "prefix_colum"):
                db_table.filter_by_IPV_family(IPV4,
                                              IPV6,
                                              db_table.prefix_column)
            # Creates indexes
            db_table.create_index()
            # Deletes duplicates in the table
            db_table.delete_duplicates()


########################
### Helper Functions ###
########################

    
    def _parse_common_elements(self, row: bs4.element.Tag):
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
        except AttributeError:
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
        return as_info, utils.get_tags(url, "td")

    
    def _parse_as_info(self, as_info: str):
        """Performs regex on as_info to return AS number and AS name.

        This is a mess, but that's because parsing html is a mess.
        """

        # If the as_info is "N/A" and the regex returns nothing
        if (as_parsed := self._as_regex.search(as_info)) is None:
            # Sometimes we can get this
            try:
                return None, re.findall(r'\d+', as_info)[0]
            # Sometimes not
            except IndexError:  # Should not use bare except
                return None, None
        else:
            # This is the first way the string can be formatted:
            if as_parsed.group("as_number") not in [None, "", " "]:
                return as_parsed.group("as_name"), as_parsed.group("as_number")
            # This is the second way the string can be formatted:
            elif as_parsed.group("as_number2") not in [None, "", " "]:
                return as_parsed.group("as_name2"),\
                    as_parsed.group("as_number2")

    
    def _format_temp_row(self) -> list:
        """Formats row vals for input into the csv files.

        _id columns are excluded from the columns.
        """

        # Quotes need to be replaced because it screws up csv insertion
        # for like that one stupid AS that has a quote in it's name
        return_list = []
        for column in self._columns:
            if column != "id":
                if (val := self._temp_row.get(column)) is None:
                    return_list.append(None)
                else:
                    return_list.append(val.replace('"', ""))
        # Excludes id column
        return return_list


class Hijack(Data):
    """Class for parsing Hijack events. Inherits from Data.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    table = Hijacks_Table

    
    def _parse_uncommon_info(self, as_info: str, extended_children: list):
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
        logging.debug("Parsed Hijack Row")


class Leak(Data):
    """Class for parsing Leak events. Inherits from Data.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    table = Leaks_Table
    
    def _parse_uncommon_info(self, as_info: str, extended_children: list):
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
        logging.debug("Parsed leak")


class Outage(Data):
    """Class for parsing outage events. Inherits from Data.

    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    table = Outages_Table
 
    def _parse_uncommon_info(self, as_info: str, extended_children: list):
        """Parses misc outage row info."""

        self._temp_row["as_name"], self._temp_row["as_number"] =\
            self._parse_as_info(as_info)
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        prefix_string = extended_children[
            len(extended_children) - 1].string.strip()
        # Finds all the numbers within a string
        prefix_info = self._nums_regex.findall(prefix_string)
        self._temp_row["number_prefixes_affected"] = prefix_info[0]
        self._temp_row["percent_prefixes_affected"] = prefix_info[1]
        logging.debug("Parsed Outage")
