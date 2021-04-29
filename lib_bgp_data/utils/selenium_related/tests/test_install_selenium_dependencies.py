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
import subprocess

from ..install_selenium_dependencies import install_selenium_driver
from ..sel_driver import Selenium_Driver


def is_installed():
    """Simple function to check install of selenium dependencies"""

    # Get chrome version
    chrome_version = subprocess.run("google-chrome --version",
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    check=True).stdout
    chrome_version_number = chrome_version.split(' ')[2]
    chrome_version_number = '.'.join(chrome_version_number.split('.')[0:3])

    # Get driver version
    driver_version = subprocess.run("chromedriver --version",
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    check=True).stdout
    driver_version_number = driver_version.split(' ')[1]
    driver_version_number = '.'.join(driver_version_number.split('.')[0:3])

    return chrome_version_number == driver_version_number

@pytest.mark.asrank_website_parser
def test_install_selenium_driver():
    """Tests all functions within the SeleniumDriver class.

    Test that chrome successfully installs. Also test if
    a second install causes errors.
    """

    driver_path = Selenium_Driver.driver_path

    # First remove chromedriver and make sure it is removed
    try:
        os.remove(driver_path)
        assert not os.path.exists(driver_path)
    except Exception:
        # if the the driver is not already on the system
        pass

    # Install the dependencies and make sure that chromedriver is installed
    install_selenium_driver()
    assert os.path.exists(driver_path)

    assert is_installed() is True

    # install again to verify that no errors occur from multiple calls
    install_selenium_driver()

    assert is_installed() is True

    # Uninstall chrome
    subprocess.run("sudo apt-get remove google-chrome-stable -y",
                   shell=True,
                   capture_output=True,
                   check=True)

    # Should return a called process error since google is uninstalled
    with pytest.raises(subprocess.CalledProcessError):
        is_installed()

    install_selenium_driver()

    assert is_installed() is True
