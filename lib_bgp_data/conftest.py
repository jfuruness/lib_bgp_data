#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file sets a pytest variable so that the logger doesn't exit nicely"""

import pytest
from datetime import datetime
from subprocess import run, check_call
from .utils import utils
from .utils.database.config import set_global_section_header, Config

__author__ = ["Justin Furuness", "Tony Zheng"]
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

#section = 'test_'

def bash(query, section=None):
    """A helper for writing SQL queries to be used with psql"""
    if section:
        return f"sudo -i -u postgres psql -d {section} -c '{query}'"
    else:
        return f"sudo -i -u postgres psql -c '{query}'" 

@pytest.fixture(scope="session", autouse=True)
def db_setup(request):
    """This fixture creates a new test db for every test session"""

    # I think this attribute is only really needed for the postgres restart
    # command in config? But it's a property so it's hard to rewrite.
    pytest.global_running_test = True

    # Underscores are like the only character I can use here that SQL allows
    section = 'test_' + utils.now().strftime('%Y_%m_%d_%H_%M_%S')
    #set_global_section_header(section)

    Config(section).install()

    # Look for and drop any test dbs that are older than 1 week
    # Done by parsing the SQL output of listing all dbs for their dates
    b = bash('SELECT datname FROM pg_database;')
    result = run(b, shell=True, check=True, capture_output=True, text=True)

    for db in result.stdout.split('\n')[2:-3]:
        if 'test_2' in db:
            d = db.split('_')
            db_date = datetime(int(d[1]), int(d[2]), int(d[3]))

            difference = datetime.now() - db_date

            if difference.days >= 7:
                check_call(bash(f'DROP DATABASE {db};'), shell=True)
 
    # everything after yield serves as the teardown
    yield
    check_call(bash(f'DROP DATABASE {section};'), shell=True)

