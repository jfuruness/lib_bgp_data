#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file sets a pytest variable so that the logger doesn't exit nicely"""

import pytest
from subprocess import run, check_call
from datetime import datetime
from .utils.database import config 
from .utils.database import Postgres
from .utils import utils

__author__ = ["Justin Furuness", "Tony Zheng"]
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import os

def pytest_runtest_setup():
    # used for postgres restart command in config.py
    # and random page cost and ulimit in postgres.py
    # https://docs.pytest.org/en/6.0.1/example/simple.html#pytest-current-test-environment-variable
    os.environ["PYTEST_CURRENT_TEST"] = "why doesn't this work"

    # Underscores are like the only character I can use here that SQL allows
    section = test_prepend() + datetime.now().strftime(test_db_fmt())
    large_db = pytest.config.getoption('--large_db')
    print(large_db)
    config.Config(section).install(large_db=large_db, restart=large_db)
 
def pytest_runtest_teardown():
    drop_old_test_databases()
    section = config.global_section_header
    check_call(Postgres.get_bash(f'DROP DATABASE {section};'), shell=True)

def drop_old_test_databases():
    # Look for and drop any test dbs that are older than 1 week
    # Done by parsing the SQL output of listing all dbs for their dates
    result = run(Postgres.get_bash('SELECT datname FROM pg_database;'),
                 shell=True,
                 check=True,
                 capture_output=True,
                 text=True)

    for db_name in result.stdout.split('\n')[2:]:
        if test_prepend() in db_name:
            db_date = datetime.strptime(db_name.replace(test_prepend(), "").strip(),
                                        test_db_fmt())

            if (datetime.now() - db_date).days >= 7:
                check_call(Postgres.get_bash(f'DROP DATABASE {db_name};'),
                           shell=True)

def pytest_addoption(parser):
    parser.addoption('--large_db', action='store_true',
                                   default=False,
                                   help='Set pytest to drop databases, restart, install max database')

def test_db_fmt():
    return '%Y_%m_%d_%H_%M_%S'

def test_prepend():
    return "test_"
