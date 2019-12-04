#!/usr/bin/env python3
# -*- codingL utf-8 -*-

import pytest
from subprocess import check_output, check_call
from ..install import Install
from ..utils import db_connection
from ..config import Config
from ...relationships_parser import Relationships_Parser
from multiprocessing import Process


def test_config():
    """This will test if two seperate installations can be created"""

    # Try installing two different sections
    Install("test1").install()
    Install("test2").install()
    # Make sure those sections are in the config file
    bash = "cat /etc/bgp/bgp.conf| grep "
    assert "test1" in check_output(bash + "test1", shell=True, text=True)
    assert "test2" in check_output(bash + "test2", shell=True, text=True)


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


def test_cleanup():
    """This is just to delete the sections created in these tests"""

    # Redundant but the Config initializer needs the section header
    Config("test1")._remove_old_config_section("test1")
    Config("test2")._remove_old_config_section("test2")
    # Delete the databases
    bash_1 = "sudo -i -u postgres psql -c 'DROP DATABASE "
    bash_2 = ";'"
    check_call(bash_1 + "test1" + bash_2, shell=True)
    check_call(bash_1 + "test2" + bash_2, shell=True)

#############
## Helpers ##
#############

def parser(section):
    """Helper function for new processes to use.

    Need this because initializing one parser after another overwrites
    the global_section_header variable that both refer to.
    """

    # Initialize relationships parser
    par = Relationships_Parser(section)
    # Parse files into database
    par.parse_files()
