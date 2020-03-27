#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Asrank_Website_Parser

The purpose of this class is to parse the information of Autonomous
Systems from asrank.caida.org. This information is then stored
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


__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from threading import Thread
import logging
import math
import time
from tqdm import tqdm

from .constants import Constants
from .sel_driver import SeleniumDriver
from .asrank_data import ASRankData
from .install_selenium_dependencies import run_shell
from .mt_tqdm import MtTqdm


class ASRankWebsiteParser:
    """Parses the AS rank, AS num, organization, country, and
    cone size from the https://asrank.caida.org/ website into a database.

    For a more in depth explanation, read the top of the file.
    Attributes:
    """

    def __init__(self):
        self._asrank_data = None
        self._total_entries = None
        self._total_pages = None
        self._mt_tqdm = None
        self._init()

    def _init(self):
        """Initialize the variables and lists that
        contain the information that will be parsed
        """
        run_shell()
        with SeleniumDriver() as sel_driver:
            self._total_pages = self._find_total_pages(sel_driver)
        self._asrank_data = ASRankData(self._total_entries)
        self._mt_tqdm = MtTqdm(100 / self._total_pages)

    def _produce_url(self, page_num, table_entries=Constants.ENTRIES_PER_PAGE):
        """Create a URL of the website with the intended
        page number and page size where page size is less than 1000

        Args:
            page_num (int): The number of the current page
            table_entries (int): The number of entries found
                within the table on the current page

        Returns:
            The string of the of the URL that will be on the
            given page and have the given number of table entries
        """
        if table_entries > Constants.ENTRIES_PER_PAGE:
            table_entries = Constants.ENTRIES_PER_PAGE
        elif table_entries < 1:
            table_entries = 1
        var_url = '?page_number=%s&page_size=%s&sort=rank' % (page_num,
                                                              table_entries)
        return Constants.URL + var_url

    def _find_total_pages(self, sel_driver):
        """Returns the total number pages of the website
        depending on the entries per page
        """
        soup = sel_driver.get_page(self._produce_url(1, 1))
        self._total_entries = max([int(page.text)
                                   for page in soup.findAll('a',
                                                            {'class':
                                                             'page-link'})
                                   if '.' not in page.text])
        return math.ceil(self._total_entries / Constants.ENTRIES_PER_PAGE)

    def _run_parser(self, t_id, total_threads):
        """Parses the website saving information on the AS rank,
        AS number, organization, country, and cone size
        """
        with SeleniumDriver() as sel_driver:
            for page_num in range(t_id, self._total_pages, total_threads):
                prev = time.time()
                soup = sel_driver.get_page(self._produce_url(page_num + 1))
                tds_lst = soup.findAll('td')
                self._asrank_data.insert_data(page_num, tds_lst)
                self._mt_tqdm.update()

    def _run_mt(self):
        """Parse asrank website using threads for separate pages"""
        threads = []
        num_threads = self._total_pages // 6
        for i in range(num_threads):
            thread = Thread(target=self._run_parser, args=(i, num_threads))
            threads.append(thread)
            thread.start()
        for th in threads:
            th.join()

    def run(self):
        """Run the multithreaded ASRankWebsiteParser"""
        start = time.time()
        self._run_mt()
        self._mt_tqdm.close()
        total_time = time.time() - start
        print('total time taken:',
              total_time,
              'seconds,',
              total_time / 60,
              'minutes',
              total_time / 3600,
              'hours')
        self._asrank_data.insert_data_into_db()
