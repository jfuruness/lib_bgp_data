#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains AS_Rank_Website_Parser which parses AS Rank data

see: https://github.com/jfuruness/lib_bgp_data/wiki/AS-Rank-Parser"""


__author__ = "Abhinna Adhikari, Sam Kasbawala, Justin Furuness"
__credits__ = ["Abhinna Adhikari", "Sam Kasbawala", "Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

import os
import random
import re
import time

from tqdm import trange, tqdm

from .tables import AS_Rank_Table

from ...utils import utils
from ...utils.base_classes import Parser
from ...utils.selenium_related.sel_driver import Selenium_Driver


class AS_Rank_Website_Parser(Parser):
    """Parses the AS rank data from https://asrank.caida.org/

    For a more in depth explanation:
    https://github.com/jfuruness/lib_bgp_data/wiki/AS-Rank-Parser
    """

    __slots__ = []

    url = 'https://asrank.caida.org/'

    def _run(self, random_delay=False):
        """Parses the AS rank data from https://asrank.caida.org/

        For a more in depth explanation:
        https://github.com/jfuruness/lib_bgp_data/wiki/AS-Rank-Parser
        """

        # Clear the ASRankTable before every run
        with AS_Rank_Table(clear=True) as _:
            pass

        # If running lots in parallel, does this so as not to DOS asrank
        if random_delay:
            print("Sleeping for ~1min")
            time.sleep(random.random() * 20)

        ### Sequential ###
        # Start from 1 because page 0 and page 1 are the same
        #for page in trange(1, self._total_pages, desc="Parsing AS Rank"):
        #    self._parse_page(page)

        with utils.Pool(None, 1, "AS Rank Parser") as pool:
            r = list(tqdm(pool.imap(self._parse_page,
                                    [page for page in range(1, self._total_pages)]),
                          total=self._total_pages-1,
                          desc="AS Rank pages"))

    def _parse_page(self, page_num):
        """Parses a page, gets AS rank, ASN, org, country, cone size"""

        with Selenium_Driver() as sel_driver:
            # Gets beautiful soup of the page
            soup = sel_driver.get_page(self._format_page_url(page_num))
            # Get all table rows, and skip the header
            rows = soup.findChildren("tr")[1:]
            # Parse all the rows, format for db insertion
            db_rows = [self._parse_row(row) for row in rows]
            # Insert the page into the database
            path = os.path.join(self.csv_dir, f"{page_num}.csv")
            utils.rows_to_db(db_rows, path, AS_Rank_Table, clear_table=False)

    def _parse_row(self, row):
        """Parse a list of five HTML table cells (tds)

        These make up a single row on asrank.caida.org
        and then return the parsed row as a list for db insertion
        """

        new_row = []
        for col_ind, attr in enumerate(row.findChildren("td")):
            # If organization column is unknown
            if col_ind == 2 and attr.text == "unknown":
                new_row.append(None)
            # This is for country, with special html
            elif col_ind == 3:
                # Format: <td ... ><span class="... flag-icon-se"></span></td>
                try:
                    new_row.append(re.findall(r'flag-icon-(..)', str(attr))[0])
                # Sometimes there is no country
                except IndexError:
                    new_row.append(None)
            else:
                new_row.append(attr.text)
        return new_row

    @property
    def _total_pages(self):
        """Returns the total number rows from asrank.caida.org.

        Get the first page of data. Return the max page number
        using the html from the pagination.
        """

        with Selenium_Driver() as sel_driver:
            # Gets html of the first page
            soup = sel_driver.get_page(self._format_page_url())
            # Gets maximum page number
            return max([int(page.text) for page in
                        # Format for all page numbers
                        soup.findAll('a', {'class': 'page-link'})
                        # Random link formatted this way, remove it
                        if page.text != ".."])

    def _format_page_url(self, page_num=1):
        """Create a URL of the website page with proper page num and rows"""

        # URL of the new page
        return (f'{self.url}?page_number={page_num}'
                f'&page_size=1000&sort=rank')
