#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains all of the data classes for parsing

The purpose of these classes is to parse information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. Please note that each data class inherits from the
Data class. For each data class, This is done through a series of steps.

1. Initialize the class
    -Handled in the __init__ function
    -Sets the table and the csv_path, and then calls __init__ on Data
2. Call __init__ on the parent class Data.
    -This initializes all regexes
    -The data list of all events of that type is also initialized
3. Rows are appended to each data class
    -This is handled by the BGPStream_Website_Parser class
    -The append function is overwritten in the parent Data class
4. For each row, parse the common elements
    -Handled by the append _parse_common_elements in the Data class
    -Gets all information that is generic to all events
5. Pass extra information to the _parse_uncommon_elements function
    -This is a function specified by each subclass
    -This function parses elements that are specific to that event type
6. Then the row is formatted for csv insertion and appended to self.data
    -Formatting is handled by the _format_temp_row() in the Data Class
7. Later the BGPStream_Website_Parser will call the db_insert function
    -This is handled in the parent Data class
    -This will insert all rows into a CSV
        -This is done because CSVs have fast bulk insertion time
    -The CSV will then be copied into the database
8. After the data is in the database, the tables will be formatted
    -First the tables remove unwanted IPV4 and IPV6 values
    -Then an index is created if it doesn't exist
    -Then duplicates are deleted if they exist
    -Then temporary tables are created
        -These are tables that are subsets of the overall data

Design Choices (summarizing from above):
    -A parent data class is used because many functions are the same
     for all data types
    -This is a mess, parsing this website is messy so I will leave it
    -Parsing is done from the last element to the first element
        -This is done because not all pages start the same way

Possible Future Extensions:
    -Add test cases
    -Ask bgpstream.com for an api?
        -It would cause less querying of their site
"""


#from ..utils import utils, error_catcher, db_connection
#from .tables import Hijack_Table, Outage_Table, Leak_Table

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import os

from constants import Constants



class SeleniumDriver:

    def __init__(self):
        self._driver = self._init_driver()

    def __enter__(self):
        if not self._driver:
            self._driver = self._init_driver()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def _init_driver(self):
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

    def get_page(self,
                 url,
                 timeout=20,
                 dynamic_class_name="asrank-row-org"):

        """Run the url on the driver to get dynamic HTML of
        a page and then create beautiful soup object of the HTML page

        Args:
            url (str): The URL that will be run on the driver
            timeout (int): The amount of time for the request to timeout
            dynamic_class_name (str): The name of a class that is only
                visible once the dynamic html is created. Indicator that 
                the dynamic HTML has been created. 

        Returns:
            A BeautifulSoup object made from the dyamic HTML
            retrived using selenium's chrome webdriver

        """
        self._driver.get(url)

        # Wait for the page to load dynamically
        wait = WebDriverWait(self._driver, timeout)
        wait.until(EC.visibility_of_element_located(
            (By.CLASS_NAME, dynamic_class_name)))

        # Extract the html and then use it to create a beautiful soup object
        data = self._driver.page_source
        soup = BeautifulSoup(data, "html.parser")
        return soup

    def close(self):
        if self._driver:
            self._driver.close()

    def get_driver(self):
        return self._driver
        
