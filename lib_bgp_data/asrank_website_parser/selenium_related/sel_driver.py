#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains an abstraction of a Selenium Chrome webdriver.

The purpose of this class is to simplify the use of
chromedriver by abstracting the various functions
and initialization into an easy-to-use class/ context manager.

Design Choices (summarizing from above):
    -Allow the class to be initialized as a context manager
        -This is done to automatically handle closing chromedriver instance

Possible Future Extensions:
    -Add test cases
"""


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

from ..constants import Constants


class SeleniumDriver:
    """Class where Selenium webdriver functions are abstracted to simplify
    code. For a more in depth explanation see the top of the file.

    Attributes:
        _driver: selenium.webdriver.Chrome, An instance of a selenium
            chromedriver.
    """

    def __init__(self):
        self._driver = self._init_driver()

    def __enter__(self):
        """Allows the SeleniumDriver to be
        instantiated using a context manager.

        Returns:
            The class itself.
        """
        if not self._driver:
            self._driver = self._init_driver()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit the context manager by closing the selenium driver."""
        self.close()

    def _init_driver(self):
        """Initialize the headless chrome webdriver
        that is used to retrieve the dynamic HTML.

        Returns:
            A headless selenium.webdriver.Chrome object.
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        path = os.path.join(Constants.CHROMEDRIVER_PATH,
                            Constants.CHROMEDRIVER_NAME)
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
        """Close the selenium driver."""
        if self._driver:
            self._driver.close()
