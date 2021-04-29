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

import requests
import subprocess
import os

from .. import utils


def install_selenium_driver():
    """Downloads all the dependencies necessary for selenium as well
    as the newest version of chrome and chromedriver.
    """

    print("Selenium driver dependencies are not installed. Installing now.")

    installing_chrome_cmds = ['wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb',
                              'sudo apt install -y ./google-chrome-stable_current_amd64.deb',
                              'rm google-chrome-stable_current_amd64.deb',
                              'sudo apt-get update',
                              ('sudo apt-get install -y unzip'
                               ' xvfb libxi6 libgconf-2-4'),
                              'yes | sudo apt-get remove google-chrome-stable',
                              'sudo apt-get -y update',
                              'sudo apt-get -y install google-chrome-stable',
                              ('wget -O /tmp/LATEST_RELEASE '
                               '"https://chromedriver.storage.googleapis.com/'
                               'LATEST_RELEASE"')]

    if os.path.exists("/etc/apt/sources.list.d/google-chrome.list"):
        with open("/etc/apt/sources.list.d/google-chrome.list", "r") as f:
            for line in f:
                if "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" in line:
                    break
            else:
                installing_chrome_cmds.insert(3,
                                              'sudo bash -c "echo \'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\' >> /etc/apt/sources.list.d/google-chrome.list"')
    else:
        installing_chrome_cmds.insert(3,
                                      'sudo bash -c "echo \'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\' >> /etc/apt/sources.list.d/google-chrome.list"')

    utils.run_cmds(installing_chrome_cmds)

    chrome_version = subprocess.run("google-chrome --version", shell=True, capture_output=True, text=True).stdout
    chrome_version_number = chrome_version.split(' ')[2]
    chrome_version_number = '.'.join(chrome_version_number.split('.')[0:3])

    source = requests.get(f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version_number}")
    chrome_driver_version = source.text

    installing_chromedriver_cmds = [f'wget "https://chromedriver.storage.googleapis.com/{chrome_driver_version}/chromedriver_linux64.zip"',
                                    'unzip chromedriver_linux64.zip',
                                    'sudo chmod +x chromedriver',
                                    'sudo mv chromedriver /usr/bin',
                                    'rm -r chromedriver_linux64.zip']
    utils.run_cmds(installing_chromedriver_cmds)
