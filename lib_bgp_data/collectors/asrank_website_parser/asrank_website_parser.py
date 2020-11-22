#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ASrank_Website_Parser.

The purpose of this class is to parse the information of Autonomous
Systems from asrank.caida.org. This information is then stored
in the database. This is done through a series of steps.

1. Initialize the asrank_data classes that will store the data as rows
    -Handled in the __init__ function
    -This class deals with inserting the data into a list of list,
     which contains the rows and then eventually into the database
2. All rows/pages are recieved from the main page of the website
    -This is handled within the _run_parser method
    -The _run_parser method uses get_page method within SeleniumDriver class
    -The _run_parser method then inserts rows into the ASRankData class
3. The data for each row is parsed within the ASRankData class
    -The insert_data method is given a row of HTML and parses the data from it
4. Rows and pages are iterated over until all the rows are parsed
    -The threads split up the pages so that there will be no
     interference from other threads
5. Call the insert_data_into_db method within the asrank_data class
    -This method will insert the parsed data into the database

Design Choices (summarizing from above):
    -Only the five attribute table found on the front of asrank are parsed
    -Multiprocessing is used

Possible Future Extensions:
    -Add test cases
"""


__author__ = "Abhinna Adhikari, Sam Kasbawala"
__credits__ = ["Abhinna Adhikari", "Sam Kasbawala"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import math
import os

from tqdm import tqdm

from .selenium_related.sel_driver import SeleniumDriver
from .tables import ASRankTable

from ...utils import utils
from ...utils.base_classes import Parser

class ASRankWebsiteParser(Parser):
    """Parses the AS rank, AS num, organization, country, and
    cone size from the https://asrank.caida.org/ website into a database.
    For a more in depth explanation, read the top of the file.

    Attributes:
        _total_rows: int, The total number of rows on asrank.caida.org
    """

    __slots__ = ['_total_rows']

    rows_per_page = 1000
    url = 'https://asrank.caida.org/'

    def __init__(self, **kwargs):
        """Initialize the variables and lists that
        contain the information that will be parsed.
        """

        super(ASRankWebsiteParser, self).__init__(**kwargs)
        self._total_rows = self._find_total_rows()

        # Clear the ASRankTable before every run
        with ASRankTable(clear=True) as _:
            pass

    def _produce_url(self, page_num, table_rows):
        """Create a URL of the website with the intended
        page number and page size where page size is less than 1000.

        Args:
            page_num: int, The number of the current page.
            table_rows: int, The number of rows found
                within the table on the current page.

        Returns:
            The string of the of the URL that will be on the
            given page and have the given number of table rows.
        """

        assert 1 <= table_rows <= self.rows_per_page, "Invalid number of rows per page"
        var_url = f'?page_number={page_num}&page_size={table_rows}&sort=rank'
        return self.url + var_url

    def _find_total_rows(self):
        """Returns the total number rows of the table.

        Returns:
            The total number of rows of the main table that are found
            on asrank.caida.org.
        """

        with SeleniumDriver() as sel_driver:
            soup = sel_driver.get_page(self._produce_url(1, 1))
            total_rows = max([int(page.text)
                              for page in soup.findAll('a',
                                                       {'class':
                                                        'page-link'})
                              if '.' not in page.text])
        return total_rows

    def _parse_row(self, tds_lst):
        """Parse a list of five HTML table cells (tds)
        that make up a single row on asrank.caida.org
        and then return the parsed row as a list.

        Args:
            tds_lst: list, Contains five HTML table cells found on
                a row in the HTML of a page_num on asrank.caida.org.

        Returns:
            A list of strings. The list contains the parsed
            HTML table cells (tds).
        """

        new_row = []
        for col_ind, attr in enumerate(tds_lst):
            if col_ind == 3:
                country = str(attr)[-16:-14]
                new_row.append(country)
            else:
                new_row.append(attr.text)
        return new_row

    def _parse_page(self, page_num):
        """Parses the website saving information on the AS rank,
        AS number, organization, country, and cone size.

        Args:
            t_id: int, The id of the current thread.
            total_threads: int, The total amount of threads running.
        """

        with SeleniumDriver() as sel_driver:
            url = self._produce_url(page_num + 1, self.rows_per_page)
            soup = sel_driver.get_page(url)
            table = soup.findChildren('table')[0]
            rows = table.findChildren('tr')

            parsed_rows = []
            for i in range(1, len(rows)):
                parsed_rows.append(self._parse_row(rows[i].findChildren('td')))

            # Insert the page into the database
            csv_file_name = self.__class__.__name__ + str(page_num)
            csv_path = os.path.join(self.csv_dir, csv_file_name) + '.csv'
            utils.rows_to_db(parsed_rows, csv_path, ASRankTable, False)

    def _run(self):
        """Run the multiprocessed ASRankWebsiteParser.
        Parse asrank website using processes for separate pages.
        """

        total_pages = math.ceil(self._total_rows / self.rows_per_page)
        with ProcessPoolExecutor(max_workers=cpu_count() * 2) as executor:
            pages = {executor.submit(self._parse_page,
                                     pg): pg for pg in range(total_pages)}

            # Handles the tqdm progress bar
            kwargs = {'total': len(pages),
                      'unit': 'it',
                      'unit_scale': True,
                      'leave': True,
                      'desc': "Parsing as rank"}
            for _ in tqdm(as_completed(pages), **kwargs):
                pass
