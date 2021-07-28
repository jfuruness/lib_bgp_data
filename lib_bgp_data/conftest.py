#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file sets a pytest variable so that the logger doesn't exit nicely"""

import pytest
from subprocess import run, check_call
from datetime import datetime
from .utils.database import config
from .utils.database import Postgres
from .utils.database import Database
from .utils import utils

__author__ = ["Justin Furuness", "Tony Zheng"]
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import os

# these are called initialization hooks
# https://docs.pytest.org/en/latest/reference.html#initialization-hooks

def pytest_sessionstart():
    # used for postgres restart command in config.py
    # and random page cost and ulimit in postgres.py
    # https://docs.pytest.org/en/latest/example/simple.html#pytest-current-test-environment-variable
    os.environ["PYTEST_CURRENT_TEST"] = "why doesn't this work"
    
    # Underscores are like the only character I can use here that SQL allows
    section = test_prepend() + datetime.now().strftime(test_db_fmt())
    config.Config(section).install()
    config.global_section_header = section

def pytest_sessionfinish():
    drop_old_test_databases()
    section = config.global_section_header
    Postgres.erase_db(section)

def pytest_runtest_teardown():

    # https://stackoverflow.com/questions/3327312/how-can-i-drop-all-the-tables-in-a-postgresql-database
    cmds = ['DROP SCHEMA public CASCADE;',
            'CREATE SCHEMA public;',
            'GRANT ALL ON SCHEMA public TO postgres;',
            'GRANT ALL ON SCHEMA public TO public;']

    with Database() as db:
        for cmd in cmds:
            db.execute(cmd)

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
            try:
                db_date = datetime.strptime(db_name.replace(test_prepend(), "").strip(),
                                            test_db_fmt())
            except ValueError:
                db_date = None
    
            if db_date and (datetime.now() - db_date).days >= 3:
                Postgres.erase_db(db_name)

def test_db_fmt():
    return '%Y_%m_%d_%H_%M_%S'

def test_prepend():
    return "test_"
