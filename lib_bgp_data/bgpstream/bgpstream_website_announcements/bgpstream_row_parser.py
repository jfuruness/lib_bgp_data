#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class BGPStream_Row_Parser.

This class can parse BGPStream rows from bgpstream.com.
"""

import re
import requests
import bs4
from multiprocessing import Queue


class BGPStream_Row_Parser:
    """This class has the functionality to parse rows from bgpstream.com"""

    def __init__(self):
        """This function should never be called

        The funcs in this class are for BGPStream_Website_Parser
        """

        pass

    def _parse_row(self, row):
        """Parses a row of html into a dictionary"""

        try:
            # These are all of the tags within the row
            children = [x for x in row.children]
            row_vals = {"event_type": children[1].string.strip()}
            if row_vals["event_type"] == "Outage":
                self._parse_outage(row_vals, children)
            elif row_vals["event_type"] == "Possible Hijack":
                self._parse_hijack(row_vals, children)
            elif row_vals["event_type"] == "BGP Leak":
                self._parse_leak(row_vals, children)
            if self.parallel is not None:
                self.q.put(row_vals)
            else:
                return row_vals
        except Exception as e:
            self.logger.error("Problem parsing row: {}".format(e))
            raise e

########################################
### Event Specific Parsing Functions ###
########################################

    def _parse_outage(self, row_vals, children):
        """Parses outage tags (children) and adds data to row_vals"""

        as_info, extended_children = self._parse_common_elements(row_vals,
                                                                 children)
        row_vals["AS_name"], row_vals["AS_number"] = self._parse_as_info(
            as_info)
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        prefix_string = extended_children[
            len(extended_children) - 1].string.strip()
        # Finds all the numbers within a string
        prefix_info = self.nums_regex.findall(prefix_string)
        row_vals["number_of_prefixes_affected"] = prefix_info[0]
        row_vals["percent_of_prefixes_affected"] = prefix_info[1]
        self.logger.debug("Parsed Outage")

    def _parse_hijack(self, row_vals, children):
        """Parses hijack tags (children) and adds data to row_vals"""

        as_info, extended_children = self._parse_common_elements(row_vals,
                                                                 children)
        row_vals["expected_origin_name"], row_vals["expected_origin_number"]\
            = self._parse_as_info(as_info[1])
        row_vals["detected_origin_name"], row_vals["detected_origin_number"]\
            = self._parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        row_vals["expected_prefix"] = self.nums_regex.search(
            extended_children[end - 6].string.strip()).group(1)
        row_vals["more_specific_prefix"] = self.nums_regex.search(
            extended_children[end - 4].string.strip()).group(1)
        row_vals["detected_as_path"] = self.nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        row_vals["detected_by_bgpmon_peers"] = self.nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)
        self.logger.debug("Parsed Hijack")

    def _parse_leak(self, row_vals, children):
        """Parses leak tags (children) and adds data to row_vals"""

        as_info, extended_children = self._parse_common_elements(row_vals,
                                                                 children)
        row_vals["origin_as_name"], row_vals["origin_as_number"] =\
            self._parse_as_info(as_info[1])
        row_vals["leaker_as_name"], row_vals["leaker_as_number"] =\
            self._parse_as_info(as_info[3])
        # We must work from the end of the elements, because the number
        # of elements at the beginning may vary depending on whether or not
        # end time is specified
        end = len(extended_children)
        # Note: Group 1 because group 0 returns the entire string,
        # not the captured regex
        row_vals["leaked_prefix"] = self.nums_regex.search(
            extended_children[end - 5].string.strip()).group(1)
        leaked_to_info = [x for x in
                          extended_children[end - 3].stripped_strings]
        # We use arrays here because there could be several AS's
        row_vals["leaked_to_number"] = []
        row_vals["leaked_to_name"] = []
        # We start the range at 1 because 0 returns the string: "leaked to:"
        for i in range(1, len(leaked_to_info)):
            name, number = self._parse_as_info(leaked_to_info[i])
            row_vals["leaked_to_number"].append(number)
            row_vals["leaked_to_name"].append(name)
        row_vals["example_as_path"] = self.nums_regex.search(
            extended_children[end - 2].string.strip()).group(1)
        row_vals["detected_by_bgpmon_peers"] = self.nums_regex.search(
            extended_children[end - 1].string.strip()).group(1)
        self.logger.debug("Parsed leak")

########################
### Helper Functions ###
########################

    def _parse_common_elements(self, row_vals, children):
        """Parses common tags and adds data to row_vals

        The first argument is a dictionary for the data.
        The second argument is a list of tags to be parsed
        The first return value is the list of strings for as_info
        The second return value is a list of more tags to parse
        """

        # Must use stripped strings here because the text contains an image
        row_vals["country"] = " ".join(children[3].stripped_strings)
        try:
            # If there is just one string this will work
            as_info = children[5].string.strip()
        except:
            # If there is more than one AS this will work
            stripped = children[5].stripped_strings
            as_info = [x for x in stripped]
        row_vals["start_time"] = children[7].string.strip()
        row_vals["end_time"] = children[9].string.strip()
        row_vals["url"] = children[11].a["href"]
        row_vals["event_number"] = self.nums_regex.search(
            row_vals["url"]).group()
        url = 'https://bgpstream.com' + row_vals["url"]
        return as_info, self._get_tags(url, "td")

    def _parse_as_info(self, as_info):
        """Performs regex on as_info to return AS number and AS name"""

        # Get group objects from a regex search
        as_parsed = self.as_regex.search(as_info)
        # If the as_info is "N/A" and the regex returns nothing
        if as_parsed is None:
            return None, None
        else:
            # This is the first way the string can be formatted:
            if as_parsed.group("as_number") is not None:
                return as_parsed.group("as_name"), as_parsed.group("as_number")
            # This is the second way the string can be formatted:
            else:
                return as_parsed.group("as_name2"),\
                    as_parsed.group("as_number2")

    def _get_tags(self, url, tag):
        """Gets the html of a given url, returns a list of selected tags"""

        response = requests.get(url)
        # Raises an exception if there was an error
        response.raise_for_status()
        # Creates a beautiful soup object from the get request
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        # This is to avoid too many open file erros
        response.close()
        # Create a list of tags from the html and return them
        return [x for x in soup.select(tag)]
