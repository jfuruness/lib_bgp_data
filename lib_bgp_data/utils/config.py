#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Config that creates and parses a config.

To see the config itself, see the create_config function and view the
_config dictionary.
"""

import os
from datetime import datetime
import logging

import pytest
from configparser import ConfigParser as SCP
from configparser import NoSectionError
from psutil import virtual_memory

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def set_global_section_header(section="bgp"):
    global global_section_header
    if hasattr(pytest, 'global_running_test') and pytest.global_running_test:
        global_section_header = "test"
    else:
        global_section_header = section if section is not None else "bgp"
    return global_section_header

class Config:
    """Interact with config file"""

    __slots__ = ["path", "logger", "section"]

    
    def __init__(self, section, path="/etc/bgp/bgp.conf"):
        """Initializes path for config file."""

        self.path = path
        self.section = section
        # Declare the section header to be global so Database can refer to it
        set_global_section_header(section)

    def create_config(self, _password):
        """Creates the default config file."""

        # Do this here so that ram is set correctly
        if hasattr(pytest, 'global_running_install_test') \
           and pytest.global_running_install_test:
                # Can't take input during tests
                restart = "sudo systemctl restart postgresql@12-main.service"
        else:
                # Do this here so that ram is set correctly
                restart = self.restart_postgres_cmd

        # Creates the /etc/bgp directory
        self._create_config_dir()
        # Removes old conf section
        self._remove_old_config_section(self.section)
        # Gets ram on the machine
        _ram = int((virtual_memory().available/1000/1000)*.9)
        logging.info("Setting ram to {}".format(_ram))

        # Conf info
        _config = SCP()
        _config.read(self.path)
        _config[self.section] = {"host": "localhost",
                                 "database": self.section,
                                 "password": _password,
                                 "user": self.section + "_user",
                                 "ram": _ram,
                                 "restart_postgres_cmd": restart}
        # Writes the config
        with open(self.path, "w+") as config_file:
            _config.write(config_file)

    
    def _create_config_dir(self):
        """Creates the /etc/bgp directory."""

        try:
            os.makedirs(os.path.split(self.path)[0])
        except FileExistsError:
            logging.debug("{} exists, not creating new directory".format(
                os.path.split(self.path)[0]))

    
    def _remove_old_config_section(self, section):
        """Removes the old config file if it exists."""

        # Initialize ConfigParser
        _conf = SCP()
        # Read from .conf file
        _conf.read(self.path)
        # Try to delete the section
        try:
            del _conf[section]
        # If it doesn' exist, doesn't matter
        except KeyError:
            return
        # Otherwise, write the change to the file
        with open(self.path, "w+") as configfile:
            _conf.write(configfile)
        
    def _read_config(self, section, tag, raw=False):
        """Reads the specified section from the configuration file."""

        parser = SCP()
        parser.read(self.path)
        string = parser.get(section, tag, raw=raw)
        try:
            return int(string)
        except ValueError:
            return string

    
    def get_db_creds(self):
        """Returns database credentials from the config file."""

        # section = "bgp"
        subsections = ["user", "host", "database"]
        args = {x: self._read_config(self.section, x) for x in subsections}
        args["password"] = self._read_config(self.section,
                                             "password",
                                             raw=True)
        return args

    @property
    def ram(self):
        """Returns the amount of ram on a system."""

        return self._read_config(self.section, "ram")

    @property
    def restart_postgres_cmd(self):
        """Returns restart postgres cmd or writes it if none exists."""

        subsection = "restart_postgres_cmd"
        try:
            cmd = self._read_config(self.section, subsection)
        except NoSectionError:

            typical_cmd = "sudo systemctl restart postgresql@12-main.service"

            prompt = "Enter the command to restart postgres\n"
            prompt += "0 or Enter: "
            prompt += typical_cmd + "\n"
            prompt += "1: sudo systemctl restart postgresql: \n"
            prompt += "Custom: Enter cmd for your machine\n"
            cmd = input(prompt)
            if cmd == "" or "0":
                cmd = typical_cmd
            elif cmd == "1":
                cmd = "sudo systemctl restart postgresql"
        return cmd

    def _write_to_config(self, section, subsection, string):
        """Writes to a config file."""

        _conf = SCP()
        _conf.read(self.path)
        _conf[section][subsection] = str(string)
        with open(self.path, 'w') as configfile:
            _conf.write(configfile)
