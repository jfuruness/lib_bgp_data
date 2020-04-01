#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This python file runs the bash script that installs Selenium, the newest
version of Chrome and chromedriver if chromedriver doesn't exist within
the chromedrivers folder.
"""

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import logging
import os

from .sel_constants import SeleniumConstants


def run_shell():
    """Runs a bash script that downloads all the dependencies necessary
    for selenium as well as the newest version of chrome and chromedriver."""
    try:
        driver_path = os.path.join(SeleniumConstants.CHROMEDRIVER_PATH,
                                   SeleniumConstants.CHROMEDRIVER_NAME)
        exists = os.path.exists(driver_path)
    except FileNotFoundError:
        exists = None

    if not exists:
        logging.warning("Dependencies are not installed. Installing now.")
        print("Chromedriver doesn't exist. Installing chrome and chromedriver")
        os.system('sudo echo ""')
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.system(file_path + '/install_selenium_dependencies.sh')
    else:
        print('Chromedriver already exists\n')
