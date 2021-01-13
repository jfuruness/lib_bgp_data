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


__author__ = "Abhinna Adhikari, Justin Furuness"
__credits__ = ["Abhinna Adhikari", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup

from .install_selenium_dependencies import install_selenium_driver


class Selenium_Driver:
    """Class where Selenium webdriver functions are abstracted to simplify
    code. For a more in depth explanation see the top of the file.

    Attributes:
        _driver: selenium.webdriver.Chrome, An instance of a selenium
            chromedriver.
    """

    __slots__ = ['_driver']

    driver_path = '/usr/bin/chromedriver'

    def __init__(self):
        if not os.path.exists(self.driver_path):
            install_selenium_driver()

        options = webdriver.ChromeOptions()
        # No GUI
        options.add_argument("--headless")
        # Bypass OS Security
        options.add_argument("--no-sandbox")
        self._driver = webdriver.Chrome(self.driver_path, options=options)

    def __enter__(self):
        """Allows this to be instantiated with a context manager

        With this you don't need to worry about closing the connection
        """

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit the context manager by closing the selenium driver."""

        self.close()

    def get_page(self,
                 url,
                 retries=3,
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

        for retry in range(retries):
            try:
                self._driver.get(url)
                # Wait for the page to load dynamically
                wait = WebDriverWait(self._driver, timeout)
                wait.until(EC.visibility_of_element_located(
                    (By.CLASS_NAME, dynamic_class_name)))
                break
            except TimeoutException:
                timeout *= 2

        # Extract the html and then use it to create a beautiful soup object
        return BeautifulSoup(self._driver.page_source, "html.parser")

    def close(self):
        """Close the selenium driver instance."""

        self._driver.quit()
