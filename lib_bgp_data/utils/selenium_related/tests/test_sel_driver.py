#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the sel_driver.py file.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Abhinna Adhikari"]
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from urllib3.exceptions import MaxRetryError
import pytest

from ..sel_driver import Selenium_Driver


def driver_is_closed(driver):
    """Determines whether the driver is closed or not.

    A driver instance will error if it is closed
    and the title is tried to be found.
    """

    try:
        driver.title
        return False
    except MaxRetryError:
        return True


@pytest.mark.asrank_website_parser
class TestSeleniumDriver:
    """Tests all functions within the SeleniumDriver class."""

    def test_init_driver(self):
        """Tests producing creating a headless selenium driver."""

        with Selenium_Driver() as sel_driver:
            assert sel_driver._driver is not None

    def test_get_page(self):
        """Tests getting the dynamic html of a url.

        Checks that the dynamic html is fetched by looking
        for the dynamic class name within the HTML.
        """

        url = 'https://asrank.caida.org'
        timeout = 20
        dynamic_class = 'asrank-row-org'
        soup = Selenium_Driver().get_page(url,
                                          timeout=timeout,
                                          dynamic_class_name=dynamic_class)
        assert soup.find_all("td", {'class': dynamic_class}) != []

    def test_close(self):
        """Test if the driver instance correctly closes."""

        driver = Selenium_Driver()
        driver.close()
        assert driver_is_closed(driver._driver)
