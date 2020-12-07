#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the install_selenium_dependencies function.
For specifics on each test, see the docstrings under each function.
"""

__authors__ = ["Abhinna Adhikari"]
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "BSD"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import pytest
import os

from ..install_selenium_dependencies import install_selenium_driver
from ..sel_driver import SeleniumDriver


@pytest.mark.asrank_website_parser
def test_install_selenium_driver():
    """Tests all functions within the SeleniumDriver class.

    Test that chrome successfully installs. Also test if
    a second install causes errors.
    """

    driver_path = SeleniumDriver.driver_path

    # First remove chromedriver and make sure it is removed
    os.remove(driver_path)
    assert not os.path.exists(driver_path)

    # Install the dependencies and make sure that chromedriver is installed
    install_selenium_driver()
    assert os.path.exists(driver_path)

    # install again to verify that no errors occur from multiple calls
    install_selenium_driver()
