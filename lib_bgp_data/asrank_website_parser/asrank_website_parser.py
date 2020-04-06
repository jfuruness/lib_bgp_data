#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Asrank_Website_Parser.

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
            where the HTML will be parsed and the table attribute data
            is temporarily stored.
        _total_rows: int, The total number of rows on asrank.caida.org
    """

    __slots__ = ['_asrank_data', '_total_rows']

    rows_per_page = 1000
    url = 'https://asrank.caida.org/'
    num_threads = 20
    retries = 3

    def __init__(self, **kwargs):
        """Initialize the variables and lists that
        contain the information that will be parsed.
        """
        super(ASRankWebsiteParser, self).__init__(**kwargs)
        install_selenium_driver()

        self._total_rows = self._find_total_rows()
        self._asrank_data = ASRankData(self._total_rows)

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
        if table_rows > self.rows_per_page:
            table_rows = self.rows_per_page
        elif table_rows < 1:
            table_rows = 1
        var_url = '?page_number=%s&page_size=%s&sort=rank' % (page_num,
                                                              table_rows)
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

    def _find_total_pages(self):
        """Returns the total number pages of the website
        depending on the rows per page.

        Returns:
            The total number of pages of the main table that are found
            on asrank.caida.org given the rows_per_page.
        """
        return math.ceil(self._total_rows / self.rows_per_page)


    def _run_parser(self, t_id, total_threads):
        """Parses the website saving information on the AS rank,
        AS number, organization, country, and cone size.

        Args:
            t_id: int, The id of the current thread.
            total_threads: int, The total amount of threads running.
        """
        timeout = total_threads * 2
        with SeleniumDriver() as sel_driver:
            for page_num in range(t_id, self._find_total_pages(), total_threads):
                for retry in range(self.retries):
                    url = self._produce_url(page_num + 1, self.rows_per_page)
                    soup = sel_driver.get_page(url, timeout)
                    table = soup.findChildren('table')[0]
                    rows = table.findChildren('tr')

                    # If timeout occurs, increase the timeout rate and try again
                    if len(rows) == 1:
                        timeout += total_threads
                        continue

                    # Insert rows if no timeout and proceed to next page
                    for i in range(1, len(rows)):
                        self._asrank_data.insert_data(rows[i].findChildren('td'))
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
