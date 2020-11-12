#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file sets a pytest variable so that the logger doesn't exit nicely"""

import pytest
from subprocess import run, check_call
from .database.config import set_global_section_header, Config
from .utils import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

section = 'test'

def pytest_runtest_setup():
    pytest.global_running_test = True

    # isn't this done in the Config constructor?
    set_global_section_header(section)

    Config(section).install()
    bash = f"sudo -i -u postgres psql -d {section} -c "
    bash += "'CREATE SCHEMA IF NOT EXISTS public;'"
    check_call(bash, shell=True)

def pytest_runtest_teardown():
    """Drop all tables in public schema instead of dropping schema itself
    because we ran into errors where public schema was not found."""

    pg = f'sudo -i -u postgres psql -d {section} -c "'

    # Using an anonymous block was attempted but issues with bash evaluating
    # $$ into the PID and 'public' specifically needing single quotes
    bash = pg + "SELECT 'DROP TABLE IF EXISTS ' || quote_ident(tablename) || "
    bash += "' CASCADE;' FROM pg_tables WHERE schemaname = 'public';\""

    output = run(bash, shell=True, check=True, capture_output=True, text=True)

    for drop_cmd in output.stdout.split('\n')[2:-3]:
        check_call(pg + drop_cmd  + '"', shell=True)
