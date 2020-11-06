#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file sets a pytest variable so that the logger doesn't exit nicely"""

import pytest
from subprocess import check_call
from .database.config import set_global_section_header, Config
from .utils import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

section = f"test_{utils.now().strftime('%m_%d_%Y_%H_%M_%S')}"

def pytest_runtest_setup():
    pytest.global_running_test = True

    # isn't this done in the Config constructor?
    set_global_section_header(section)

    Config(section).install()
    bash = f"sudo -i -u postgres psql -d {section} -c "
    bash += "'CREATE SCHEMA IF NOT EXISTS public;'"
    check_call(bash, shell=True)

def pytest_runtest_teardown():
    bash = f"sudo -i -u postgres psql -d {section} -c "
    bash += "'DROP SCHEMA IF EXISTS public CASCADE;'"
    check_call(bash, shell=True)
