#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from bs4 import BeautifulSoup


def open_custom_html(url: str):
    """Function used to patch sel_driver.get_page()"""

    dir_path = os.path.dirname(os.path.realpath(__file__))
    html_path = os.path.join(os.path.join(dir_path, 'test_html'), 'page.html')
    soup = BeautifulSoup(open(html_path), 'html.parser')
    return soup
