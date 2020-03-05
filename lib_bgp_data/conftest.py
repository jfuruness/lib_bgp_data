#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file sets a pytest variable so that the logger doesn't exit nicely"""

import pytest
from subprocess import check_call
from .utils.config import set_global_section_header

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

def pytest_runtest_setup(section="test"):
    pytest.global_running_test = True
    set_global_section_header(section)
    bash = "sudo -i -u postgres psql -d test -c "
    bash += "'CREATE SCHEMA IF NOT EXISTS public;'"
    check_call(bash, shell=True)

def pytest_runtest_teardown():
    bash = "sudo -i -u postgres psql -d test -c "
    bash += "'DROP SCHEMA IF EXISTS public CASCADE;'"
    check_call(bash, shell=True)
