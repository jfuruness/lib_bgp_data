#!/usr/bin/env python3
# -*- codingL utf-8 -*-

__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from multiprocessing import Process
from subprocess import check_output, check_call

import pytest

from ..config import Config
from ...relationships_parser import Relationships_Parser

@pytest.mark.database
@pytest.mark.xfail(reason="New hire fix, problem in conftest?")
def test_parsers():
    """This will test the ability to run two parsers simultaneosuly"""

    # Use multiprocessing to run at the same time
    p1 = Process(target=parser, args=("test1",))
    p2 = Process(target=parser, args=("test2",))
    # Run the two processes
    p1.start()
    p2.start()
    # Wait for them to finish
    p1.join()
    p2.join()
    # Check that both tables' data match
    bash_1 = "sudo -i -u postgres psql -d "
    bash_2 = " -c 'select count(*) from peers;'"
    data1 = check_output(bash_1 + "test1" + bash_2, shell=True)
    data2 = check_output(bash_1 + "test2" + bash_2, shell=True)
    assert data1 == data2

@pytest.mark.database
@pytest.mark.xfail(reason="New hires fix, problem in conftest?")
def test_cleanup():
    """This is just to delete the sections created in these tests"""

    for test in ["test1", "test2"]:
        # Redundant but the Config initializer needs the section header
        Config(test)._remove_old_config_section(test)
        # Delete the databases
        bash = f"sudo -i -u postgres psql -c 'DROP DATABASE {test};'"
        check_call(bash, shell=True)


def parser(section):
    """Helper function for new processes to use.

    Need this because initializing one parser after another overwrites
    the global_section_header variable that both refer to.
    """

    # Initialize relationships parser and parses files
    Relationships_Parser(section=section).parse_files()
