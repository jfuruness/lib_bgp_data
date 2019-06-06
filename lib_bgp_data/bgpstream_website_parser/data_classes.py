#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the classes for parsing rows from bgstream.com"""

import sys
import urllib.request
import shutil
import os
import re
import requests
import bs4
from ..utils import utils, error_catcher, db_connection
from .tables import Hijack_Table, Outage_Table, Leak_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Data:
    """Class for parsing rows of bgpstream"""

    __slots__ = ['logger', 'as_regex', 'nums_regex', 'ip_regex', 'temp_row', 'data', 'columns']

    @error_catcher()
    def __init__(self, logger):
        """Initializes row instance and determine info about it"""

        self.logger = logger
        self.logger.debug("Initialized row")
        # This regex parses out the AS number and name from a string of both
        self.as_regex = re.compile(r'''
                                   (?P<as_name>.+?)\s\(AS\s(?P<as_number>\d+)\)
                                   |
                                   (?P<as_number2>\d+).*?\((?P<as_name2>.+?)\)
                                   ''', re.VERBOSE
                                   )
        # This regex returns a string that starts and ends with numbers
        self.nums_regex = re.compile(r'(\d[^a-zA-Z\(\)\%]*\d*)')
        self.ip_regex = re.compile(r'.+?:(.+)')
        self.data = []

    @error_catcher()
    def append(self, row):
        """Parses a row and appends to data list"""

        self.temp_row = {}
        as_info, extended_children = self._parse_common_elements(row)
        self._parse_uncommon_info(as_info, extended_children)
        self.data.append(self._format_temp_row())

    @error_catcher()
    def db_insert(self, start, end, IPV4=True, IPV6=False):
        utils.rows_to_db(self.logger, self.data, self.csv_path, self.table,
            clear_table=False)
        with db_connection(self.table, self.logger) as db_table:
            db_table.filter(IPV4, IPV6)
            db_table.create_index()
            db_table.delete_duplicates()
            db_table.create_temp_table(start, end)
            

########################
### Helper Functions ###
########################

    def _parse_common_elements(self, row):
        """Parses common tags and adds data to temp_row
        The first return value is the list of strings for as_info
        The second return value is a list of more tags to parse
        """

        children = [x for x in row.children]
        self.temp_row = {"event_type": children[1].string.strip()}
        # Must use stripped strings here because the text contains an image
        self.temp_row["country"] = " ".join(children[3].stripped_strings)
        try:
            # If there is just one string this will work
            as_info = children[5].string.strip()
        except:
            # If there is more than one AS this will work
            stripped = children[5].stripped_strings
            as_info = [x for x in stripped]
        self.temp_row["start_time"] = children[7].string.strip()
        self.temp_row["end_time"] = children[9].string.strip()
        self.temp_row["url"] = children[11].a["href"]
        self.temp_row["event_number"] = self.nums_regex.search(
            self.temp_row["url"]).group()
        url = 'https://bgpstream.com' + self.temp_row["url"]
        return as_info, utils.get_tags(url, "td")[0]

    def _parse_as_info(self, as_info):
        """Performs regex on as_info to return AS number and AS name"""

        # Get group objects from a regex search
        as_parsed = self.as_regex.search(as_info)
        # If the as_info is "N/A" and the regex returns nothing
        if as_parsed is None:
            try:
                return None, re.findall(r'\d+', as_info)[0]
            except:
                return None, None
        else:
            # This is the first way the string can be formatted:
            if as_parsed.group("as_number") not in [None, "", " "]:
                return as_parsed.group("as_name"), as_parsed.group("as_number")
            # This is the second way the string can be formatted:
            elif as_parsed.group("as_number2") not in [None, "", " "]:
                return as_parsed.group("as_name2"),\
                    as_parsed.group("as_number2")

    def _format_temp_row(self):
        """Formats row vals for input into the csv files"""

        return [self.temp_row.get(x) for x in self.columns]

class Hijack(Data):
    """Class for parsing Hijack events"""

    __slots__ = ['table', 'csv_path']

    @error_catcher()
    def __init__(self, logger, csv_dir):
        """Initializes row instance and determine info about it"""

        Data.__init__(self, logger)
        self.table = Hijack_Table
        self.csv_path = "{}/hijack.csv".format(csv_dir)
        with db_connection(self.table, self.logger) as t:
            self.columns = t.columns


    def _parse_uncommon_info(self, as_info, extended_children):
        """Parses misc hijack row info."""

        self.temp_row["expected_origin_name"],\
            self.temp_row["expected_origin_number"]\
                = self._parse_as_info(as_info[1])
        self.temp_row["detected_origin_name"],\
            self.temp_row["detected_origin_number"]\
                = self._parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        self.temp_row["expected_prefix"] = self.ip_regex.search(
            extended_children[end - 6].string).group(1).strip()
        self.temp_row["more_specific_prefix"] = self.ip_regex.search(
            extended_children[end - 4].string).group(1).strip()
        self.temp_row["detected_as_path"] = self.nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        self.temp_row["detected_as_path"] = str([int(s) for s in\
            self.temp_row.get("detected_as_path").split(' ')])
        self.temp_row["detected_as_path"] =\
            self.temp_row.get("detected_as_path"
                ).replace('[', '{').replace(']', '}')
        self.temp_row["detected_by_bgpmon_peers"] = self.nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)
        self.logger.debug("Parsed Hijack Row")

class Leak(Data):
    """Class for parsing Leak events"""

    __slots__ = ['table', 'csv_path']

    @error_catcher()
    def __init__(self, logger, csv_dir):
        """Initializes row instance and determine info about it"""

        Data.__init__(self, logger)
        self.table = Leak_Table
        self.csv_path = "{}/leak.csv".format(csv_dir)

    def _parse_uncommon_info(self, as_info, extended_children):
        """Parses misc leak row info."""

        self.temp_row["origin_as_name"], self.temp_row["origin_as_number"] =\
            self._parse_as_info(as_info[1])
        self.temp_row["leaker_as_name"], self.temp_row["leaker_as_number"] =\
            self._parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        self.temp_row["leaked_prefix"] = self.nums_regex.search(
            extended_children[end - 5].string.strip()).group(1).rstrip()
        leaked_to_info = [x for x in
                          extended_children[end - 3].stripped_strings]
        # We use arrays here because there could be several AS's
        self.temp_row["leaked_to_number"] = []
        self.temp_row["leaked_to_name"] = []
        # We start the range at 1 because 0 returns the string: "leaked to:"
        for i in range(1, len(leaked_to_info)):
            name, number = self._parse_as_info(leaked_to_info[i])
            self.temp_row["leaked_to_number"].append(int(number))
            self.temp_row["leaked_to_name"].append(name)
        self.temp_row["leaked_to_number"] =\
            str(self.temp_row.get("leaked_to_number")
                ).replace('[', '{').replace(']', '}')
        self.temp_row["leaked_to_name"] =\
            str(self.temp_row.get("leaked_to_name")
                ).replace('[', '{').replace(']', '}')
        example_as_path = self.nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        example_as_path = str([int(s) for s in example_as_path.split(' ')])
        self.temp_row["example_as_path"] =\
            example_as_path.replace('[', '{').replace(']', '}')
        self.temp_row["detected_by_bgpmon_peers"] = self.nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)
        self.logger.debug("Parsed leak")

class Outage(Data):
    """Class for parsing outage events"""

    __slots__ = ['table', 'csv_path']

    @error_catcher()
    def __init__(self, logger, csv_dir):
        """Initializes row instance and determine info about it"""

        Data.__init__(self, logger)
        self.table = Outage_Table
        self.csv_path = "{}/outage.csv".format(csv_dir)

    def _parse_uncommon_info(self, as_info, extended_children):
        """Parses misc outage row info."""

        self.temp_row["as_name"], self.temp_row["as_number"] =\
            self._parse_as_info(as_info)

        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        prefix_string = extended_children[
            len(extended_children) - 1].string.strip()
        # Finds all the numbers within a string
        prefix_info = self.nums_regex.findall(prefix_string)
        self.temp_row["number_prefixes_affected"] = prefix_info[0]
        self.temp_row["percent_prefixes_affected"] = prefix_info[1]
        self.logger.debug("Parsed Outage")
