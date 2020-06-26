#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Hurricane_Website_Parser

The purpose of this class is to parse the information from
https://bgp.he.net. This information is then stored in the database. This
is done in a series of steps.

1. Clear the Hurricane table
    - Handled in the _run function
2. Get the prefixes from the Hijacks table
    - Handled by the _get_prefixes function
    - This will return a list of prefexis for each row in the hijacks table
3. Get the rows for database insertion
    - Handled by the _get_roas_function
    - This uses the _get_page_from_search mfunction within SeleniumDriver
      class
4. Insert the data into the database
    - Handled in the utils.rows_to_db function
    - First converts data to a csv then inserts it into the database
    - CSVs are used for fast bulk database insertion
5. An index is created on the prefix

Possible Future Extensions:
    - Add test cases
    - Add multiporcessing, runs very slow at the moment

DISCLAIMER: The https://bgp.he.net website has query limits, making this
parser essentially useless. After filling the hijacks table, suppose there
`n` rows in it. This means that there are a minimum of `n` prefixes we will
need to query (if every hijack is a prefix hijack) or a maximum of `2n`
prefixes (if every hijack is a subprefix hijack). After testing, the parser
was only able to make it through 70-ish rows before getting the query limit
error, meaning the query limit is roughly somewhere between 70 and 140.
Considering that `n` is normally upwards of 1400, parsing the website isn't
really viable.
"""

__author__ = "Samarth Kasbawala"
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging
import re
from tqdm import tqdm
from bs4 import BeautifulSoup

from .selenium_related.sel_driver import SeleniumDriver
from .tables import Hurricane_Table
from ..bgpstream_website_parser.tables import Hijacks_Table
from ..base_classes import Parser
from ..utils import utils


class Hurricane_Website_Parser(Parser):

    __slots__ = []
    url = "https://bgp.he.net/"

    def _run(self):
        """This method runs the parser"""

        with Hurricane_Table(clear=True) as table:
            # Get the prefixes from the hijacks table
            prefixes =  self._get_prefixes()[:10]
            # Get the rows that need to be inserted from bgp.he.net
            rows = self._get_rows(prefixes)
            # Inserts the data into a CSV and then the database
            _csv_dir = f"{self.csv_dir}/hurricane.csv"
            utils.rows_to_db(rows, _csv_dir, Hurricane_Table)
            # Create an index
            table.create_index()

    def _get_prefixes(self) -> list:
        """This method returns a list of prefixes from the hijacks table"""

        with Hijacks_Table() as table:
            sql = "SELECT expected_prefix, more_specific_prefix FROM hijacks;"
            prefixes = [list(row.values()) for row in table.execute(sql)]

        return prefixes

    def _has_data(self, soup: BeautifulSoup) -> bool:
        """This method checks whether or not a given HTML page has data"""

        # If a prefix doesn't have data or there is an error
        if soup.findAll(text=re.compile('Address has 0 hosts associated with it.')) or \
           soup.findAll(id="error"):
            return False
        # This means we have reached the limit, raise an error and quit
        elif soup.findAll(id="resourceerror"):
            raise RuntimeError("Reached query limit")
        return True

    def _get_rows(self, prefixes: list) -> list:
        """This method creates a list of lists. Each list in the list
        represents a row to be inserted into the table
        """

        # The list we will be inserting each row into
        rows = []

        # Loop through the list of prefix pairs
        for prefix in tqdm(prefixes):

            # List of BeautifulSoup objects we need to parse
            soups = []

            # If it is a prefix hijack, query it once. If it is a subprefix
            # hijack, query both the subprefix and the prefix.
            with SeleniumDriver() as sel_driver:
                soups.append(sel_driver.get_page_from_search(self.url, prefix[0]))
                if prefix[0] != prefix[1]:
                    soups.append(sel_driver.get_page_from_search(self.url, prefix[1]))

            # Loop through the soup objects, max of two pages
            for soup in soups:

                # Check if there is any data or if there are any errors
                if not self._has_data(soup):
                    continue

                # Parse the page. First, we find the table that contains the
                # data. Then, we find the body of the table. Last, we find all
                # rows in the table
                data = soup.find(id="netinfo")
                table = soup.find("table")
                table_body = table.findAll("tbody")[1]
                table_rows = table_body.findAll("tr")

                # For each row in the table, get the information and store
                # in a list. Append this list to the list "rows"
                for table_row in table_rows:
                    row = []
                    for td in table_row.findAll("td"):
                        # Strip unwanted characters
                        row.append(re.sub(r"[^a-zA-Z0-9/' '.]", "", td.text))
                    rows.append(row)

        # return the rows object
        return rows

