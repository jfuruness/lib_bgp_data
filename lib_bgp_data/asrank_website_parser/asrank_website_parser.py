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

#from enum import Enum
#from ..utils import error_catcher, utils, db_connection
#from .data_classes import Leak, Hijack, Outage

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Thread
import numpy as np
import math
import time
import csv
import os

from constants import Constants
import install_selenium_dependencies as install_sel


class ASRankWebsiteParser:
    """Parses the AS rank, AS num, organization, country, and
    cone size from the https://asrank.caida.org/ website into a database.

    For a more in depth explanation, read the top of the file.
    Attributes:


    """
    def __init__(self):
        self._as_rank = None
        self._as_num = None
        self._org = None
        self._country = None
        self._cone_size = None

        self._total_entries = None
        self._total_pages = None
        self._elements_lst = None

        self._init()

    def _init(self):
        """Initialize the variables and lists that
        contain the information that will be parsed"""
        install_sel.run_shell() 
        driver = self.init_driver()
        self._total_pages = self._find_total_pages(driver)
        driver.close()

        self._as_rank = [0] * self._total_entries
        self._as_rank = [0] * self._total_entries
        self._as_num = [0] * self._total_entries
        self._org = [0] * self._total_entries
        self._country = [0] * self._total_entries
        self._cone_size = [0] * self._total_entries

        self._elements_lst = [self._as_rank,
                              self._as_num,
                              self._org,
                              self._country,
                              self._cone_size]

    def init_driver(self):
        """Initialize the headless chrome webdriver
        that is used to retrieve the dynamic HTML

        Returns:
            A headless selenium.webdriver.Chrome object

        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_driver_name = 'chromedriver'
        driver = webdriver.Chrome(os.path.join(Constants.CHROMEDRIVER_PATH, chrome_driver_name), 
                                                                        options=chrome_options)
        return driver

    def _produce_url(self, page_num, table_entries):
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
        return Constants.URL + '?page_number=%s&page_size=%s&sort=rank' % (page_num,
                                                                           table_entries)

    def _get_page(self,
                  driver,
                  page_num,
                  table_entries=Constants.ENTRIES_PER_PAGE,
                  dynamic_class_name="asrank-row-org"):
        """Run the url on the driver to get dynamic HTML of
        a page and then create beautiful soup object of the HTML page

        Args:
            page_num (int): The number of the current page
            table_entries (int): The number of entries found
                within the table on the current page
            dynamic_class_name (str): The name of a class that
                is only visible once the dynamic html is created.

        Returns:
            A BeautifulSoup object made from the dynamic HTML
            retrieved using selenium's chrome webdriver

        """
        driver.get(self._produce_url(page_num, table_entries))

        # Wait for the page to load dynamically
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located(
            (By.CLASS_NAME, dynamic_class_name)))

        # Extract the html and then use it to create a beautiful soup object
        data = driver.page_source
        soup = BeautifulSoup(data, "html.parser")
        return soup

    def _find_total_pages(self, driver):
        """Returns the total number pages of the website
        depending on the entries per page"""
        soup = self._get_page(driver, 1, 1)
        self._total_entries = max([int(page.text)
                                   for page in soup.findAll('a',
                                                            {'class': 'page-link'})
                                   if '.' not in page.text])
        return math.ceil(self._total_entries / Constants.ENTRIES_PER_PAGE)


    def _run_parser(self, t_id, total_threads):
        """Parses the website saving information on the AS rank,
        AS number, organization, country, and cone size"""
        driver = self.init_driver()
        total_time = 0
        for page_num in range(t_id, self._total_pages, total_threads):
            prev = time.time()
            soup = self._get_page(driver, page_num + 1)
            temp_tds = soup.findAll('td')

            for i in range(0, len(temp_tds) // len(self._elements_lst)):
                for j, element in enumerate(self._elements_lst):
                    temp_ind = i * len(self._elements_lst) + j
                    el_ind = page_num * Constants.ENTRIES_PER_PAGE + i

                    if j != 3:
                        if j == 2 and len(temp_tds[temp_ind].text) == 0:
                            element[el_ind] = 'unknown'
                        else:
                            element[el_ind] = temp_tds[temp_ind].text
                    else:
                        element[el_ind] = str(temp_tds[temp_ind])[-16: -14]

            print('time taken on page #' + str(page_num) + ': ',
                  time.time() - prev)
            total_time += time.time() - prev

        print('temp time taken:',
              total_time,
              'seconds,',
              total_time / 60,
              'minutes',
              total_time / 3600,
              'hours')
        driver.close()

    def print_table(self):
        """Print out a table of the information
        parsed from the website

        In the form for each row:

        as_rank   as_number   organization   country_abbreviation   cone_size
        """
        max_org = ''
        for org in self._org:
            if len(org) > len(max_org):
                max_org = org

        for i in range(len(self._elements_lst[0])):
            line = ''
            for j, el in enumerate(self._elements_lst):
                line += str(el[i])
                if el is self._org:
                    line += ' ' * (len(max_org) - len(el[i]))
                line += '\t\t' if j != len(self._elements_lst) - 1 else '\n'
            print(line)

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

    def write_csv(self, csv_path):
        with open(csv_path, mode='w') as temp_csv:
            csv_writer = csv.writer(temp_csv, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for i in range(len(self._as_rank)):
                row = [lst[i] for lst in self._elements_lst]
                csv_writer.writerow(row)

    def run(self):
        start = time.time()
        self._run_mt()

        total_time = time.time() - start
        print('total time taken:', total_time, 'seconds,', total_time / 60, 'minutes', total_time / 3600, 'hours')
        self.write_csv(Constants.CSV_FILE_NAME)
        #utils.csv_to_db(ASRank_Table, Constants.CSV_FILE_NAME, True)


if __name__ == '__main__':
    ASRankWebsiteParser().run()
    
    
#!/usr/bin/env python3
