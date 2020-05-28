#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This python file runs installs the newest version
of chrome and chromedriver if chromedriver doesn't
exist within the chromedrivers folder.
"""

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import logging

from ...utils import utils


def install_selenium_driver():
    """Downloads all the dependencies necessary for selenium as well
    as the newest version of chrome and chromedriver.
    """

    logging.warning("Selenium driver dependencies are not installed. Installing now.")

    installing_chrome_cmds = ['sudo apt-get update',
                              'sudo apt-get install -y unzip xvfb libxi6 libgconf-2-4',
                              'yes | sudo apt-get remove google-chrome-stable',
                              'sudo bash -c "echo \'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\' >> /etc/apt/sources.list.d/google-chrome.list"',
                              'sudo apt-get -y update',
                              'sudo apt-get -y install google-chrome-stable',
                              'wget -O /tmp/LATEST_RELEASE "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"']
    utils.run_cmds(installing_chrome_cmds)

    installing_chromedriver_cmds = ['wget "https://chromedriver.storage.googleapis.com/$(cat /tmp/LATEST_RELEASE)/chromedriver_linux64.zip"',
                                    'unzip chromedriver_linux64.zip',
                                    'sudo chmod +x chromedriver',
                                    'sudo mv chromedriver /usr/bin',
                                    'rm -r chromedriver_linux64.zip']
    utils.run_cmds(installing_chromedriver_cmds)
