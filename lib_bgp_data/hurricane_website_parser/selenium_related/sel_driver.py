#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains an abstraction of a Selenium Chrome webdriver.

The purpose of this class is to simplify the use of
chromedriver by abstracting the various functions
and initialization into an easy-to-use class/ context manager.
chromedriver must be found at the path, driver_path class
variable, within the SeleniumDriver class.

Design Choices (summarizing from above):
    -Allow the class to be initialized as a context manager
        -This is done to automatically handle closing chromedriver instance

Possible Future Extensions:
    -Add test cases
"""


__authors__ = ["Abhinna Adhikari", "Samarth Kasbawala"]
__credits__ = ["Abhinna Adhikari", "Samarth Kasbawala"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import logging
import os

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from bs4 import BeautifulSoup

from .install_selenium_dependencies import install_selenium_driver


class SeleniumDriver:
    """Class where Selenium webdriver functions are abstracted to simplify
    code. For a more in depth explanation see the top of the file.

    Attributes:
        _driver: selenium.webdriver.Chrome, An instance of a selenium
            chromedriver.
    """

    __slots__ = ['_driver']

    driver_path = '/usr/bin/chromedriver'
    retries = 3

    def __init__(self):
        if not os.path.exists(self.driver_path):
            install_selenium_driver()
        self._driver = SeleniumDriver.init_driver()

    def __enter__(self):
        """Allows the SeleniumDriver to be
        instantiated using a context manager.

        Returns:
            The class itself.
        """

        if not self._driver:
            self._driver = SeleniumDriver.init_driver()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit the context manager by closing the selenium driver."""

        self.close()

    @staticmethod
    def init_driver():
        """Initialize the headless chrome webdriver
        that is used to retrieve the dynamic HTML.

        The --headless argument makes sure that chrome is run headless

        Returns:
            A headless selenium.webdriver.Chrome object.
        """

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        path = os.path.join(SeleniumDriver.driver_path)
        driver = webdriver.Chrome(path, options=chrome_options)
        return driver

    def get_page(self,
                 url,
                 timeout=20,
                 dynamic_class_name="asrank-row-org"):
        """Run the url on the driver to get dynamic HTML of
        a page and then create beautiful soup object of the HTML page.

        Args:
            url: str, The URL that will be run on the driver.
            timeout: int, The amount of time for the request to timeout.
            dynamic_class_name: str, The name of a class that is only
                visible once the dynamic html is created. Indicator that
                the dynamic HTML has been created.

        Returns:
            A BeautifulSoup object made from the dyamic HTML
            retrived using selenium's chrome webdriver.
        """

        for retry in range(self.retries):
            try:
                self._driver.get(url)
                # Wait for the page to load dynamically
                wait = WebDriverWait(self._driver, timeout)
                wait.until(EC.visibility_of_element_located(
                    (By.CLASS_NAME, dynamic_class_name)))
            except TimeoutException:
                timeout *= 2
                continue
            break

        # Extract the html and then use it to create a beautiful soup object
        data = self._driver.page_source
        soup = BeautifulSoup(data, "html.parser")
        return soup

    def get_page_from_search(self,
                             url,
                             search_input,
                             timeout=10,
                             search_id="search_search",
                             dynamic_id_name="error"):
        """Run the url on the driver and search on the website to get a
        dynamic HTML of a page and then create a beautiful soup object of the
        HTML page

        Args:
            url: str, The URL that will be run on the driver.
            search_input: str, The string that will be searched on the website
            timeout: int, The amount of time for the request to timeout.
            search_id: str, The name of the id the site uses for its search
                input.
            dynamic_id_name: str, The name of an id that is only invisible
                once the dynamic html is created. Indicator that the dynamic
                HTML has been created.

        Returns:
            A BeautidulSoup object made from the dynamic HTML retrieved using
            selenium's chrome webdriver
        """

        # Go to the home page
        self._driver.get(url)

        # Search the input on the site
        search = self._driver.find_element_by_id(search_id)
        search.send_keys(search_input)
        search.send_keys(Keys.RETURN)

        # Wait for the search to go through
        try:
            wait = WebDriverWait(self._driver, timeout)
            wait.until(EC.invisibility_of_element_located(
                (By.ID, dynamic_id_name)))
        except TimeoutException:
            pass

        # Get the HTML and return the BeautifulSoup object
        data = self._driver.page_source
        soup = BeautifulSoup(data, "html.parser")
        return soup

    def close(self):
        """Close the selenium driver instance."""

        self._driver.quit()

