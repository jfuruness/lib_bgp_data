#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Asrank_Website_Parser.

The purpose of this class is to parse the information of Autonomous
Systems from asrank.caida.org. This information is then stored
in the database. This is done through a series of steps.

1. Initialize the asrank_data classes that will store the data
    -Handled in the __init__ function
    -This class mainly deals with inserting the data into lists
     and then eventually into the database
2. All rows/pages are recieved from the main page of the website
    -This is handled within the _run_parser method
    -The _run_parser method uses get_page method within sel_driver.py
3. The data is parsed within the asrank_data class
    -The insert_data method is used to insert all the rows from a page
    -The insert_data method parses the HTML
4. Rows and pages are iterated over until all the rows are parsed
    -The threads split up the pages so that there will be no
     interference from other threads
5. Call the insert_data_into_db method within the asrank_data class
    -The data is converted into a csv file before inserting
    -This will parse all rows and insert them into the database

Design Choices (summarizing from above):
    -Only the five attribute table found on the front of asrank is parsed
    -Multithreading is used because the task is less computationally
     intensive than IO intensive

Possible Future Extensions:
    -Add test cases
"""


__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from threading import Thread
import math

from ..base_classes import Parser
from .selenium_related.sel_driver import SeleniumDriver
from .asrank_data import ASRankData
from .selenium_related.install_selenium_dependencies import install_selenium_driver


class ASRankWebsiteParser(Parser):
    """Parses the AS rank, AS num, organization, country, and
    cone size from the https://asrank.caida.org/ website into a database.
    For a more in depth explanation, read the top of the file.

    Attributes:
        _asrank_data: ASRankData, An instance of ASRankData class
            where the HTML will be parsed and the table attributes
            are temporarily stored.
        _total_entries: int, The total number of rows on asrank.caida.org
        _total_pages: int, The total number of pages on asrank given
            entries_per_page entries per page.
    """

    __slots__ = ['_asrank_data', '_total_entries', '_total_pages']

    entries_per_page = 1000
    url = 'https://asrank.caida.org/'
    num_threads = 10
    retries = 3

    def __init__(self, **kwargs):
        """Initialize the variables and lists that
        contain the information that will be parsed.
        """
        super(ASRankWebsiteParser, self).__init__(**kwargs)
        install_selenium_driver()

        self._total_entries = None
        with SeleniumDriver() as sel_driver:
            self._total_pages = self._find_total_pages(sel_driver)
        self._asrank_data = ASRankData(self._total_entries)

    def _produce_url(self, page_num, table_entries):
        """Create a URL of the website with the intended
        page number and page size where page size is less than 1000.

        Args:
            page_num: int, The number of the current page.
            table_entries: int, The number of entries found
                within the table on the current page.

        Returns:
            The string of the of the URL that will be on the
            given page and have the given number of table entries.
        """
        if table_entries > self.entries_per_page:
            table_entries = self.entries_per_page 
        elif table_entries < 1:
            table_entries = 1
        var_url = '?page_number=%s&page_size=%s&sort=rank' % (page_num,
                                                              table_entries)
        return self.url + var_url

    def _find_total_pages(self, sel_driver):
        """Returns the total number pages of the website
        depending on the entries per page.

        Args:
            sel_driver: SeleniumDriver, An instance of the
                SeleniumDriver class.

        Returns:
            The total number of pages of the main table
            that is found on asrank.caida.org.
        """
        soup = sel_driver.get_page(self._produce_url(1, 1))
        self._total_entries = max([int(page.text)
                                   for page in soup.findAll('a',
                                                            {'class':
                                                             'page-link'})
                                   if '.' not in page.text])
        return math.ceil(self._total_entries / self.entries_per_page)

    def _run_parser(self, t_id, total_threads):
        """Parses the website saving information on the AS rank,
        AS number, organization, country, and cone size.

        Args:
            t_id: int, The id of the current thread.
            total_threads: int, The total amount of threads running.
        """
        timeout = total_threads * 2
        with SeleniumDriver() as sel_driver:
            for page_num in range(t_id, self._total_pages, total_threads):
                for retry in range(self.retries):
                    url = self._produce_url(page_num + 1, self.entries_per_page)
                    soup = sel_driver.get_page(url, timeout)
                    table = soup.findChildren('table')[0]
                    rows = table.findChildren('tr')

                    # If timeout occurs, increase the timeout rate and try again
                    if len(rows) == 1:
                        timeout += total_threads
                        continue

                    # Insert rows if no timeout and proceed to next page
                    for i, row in enumerate(rows):
                        if i != 0:  # Ignore the first row
                            self._asrank_data.insert_data(row.findChildren('td'))
                    break

    def _run_mt(self):
        """Parse asrank website using threads for separate pages."""
        threads = []
        num_threads = self.num_threads
        for i in range(num_threads):
            thread = Thread(target=self._run_parser, args=(i, num_threads))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def _run(self):
        """Run the multithreaded ASRankWebsiteParser."""
        self._run_mt()
        self._asrank_data.insert_data_into_db(self.csv_dir)
