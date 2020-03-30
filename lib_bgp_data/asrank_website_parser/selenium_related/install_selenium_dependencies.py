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
import time
import os

from ..constants import Constants


def run_shell():
    try:
        exists = os.path.exists(os.path.join(Constants.CHROMEDRIVER_PATH,
                                             Constants.CHROMEDRIVER_NAME))
    except FileNotFoundError:
        exists = None

    if not exists:
        logging.warning("Dependencies are not installed. Installing now.")
        print("Chromedriver doesn't exist. Installing chrome and chromedriver")
        os.system('sudo echo ""')
        os.system(Constants.FILE_PATH + '/install_selenium_dependencies.sh')
    else:
        print('Chromedriver already exists\n')
