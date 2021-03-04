#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Config that creates and parses a config.

To see the config itself, see the create_config function and view the
_config dictionary.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from datetime import datetime
import logging
import os

import pytest
import configparser
from configparser import NoSectionError, ConfigParser as SCP
from psutil import virtual_memory



def set_global_section_header(section=None):
    global global_section_header
    if section is not None:
        global_section_header = section
    # More readable to write it this way imo
    elif "global_section_header" in globals() and global_section_header is not None:
        pass
    else:
        global_section_header = "bgp"
    return global_section_header

class Config:
    """Interact with config file"""

    __slots__ = []

    path = "/etc/bgp/bgp.conf"
    
    def __init__(self, section: str = None):
        """Initializes path for config file."""

        # Declare the section header to be global so Database can refer to it
        set_global_section_header(section)

    @property
    def section(self):
        global global_section_header
        return global_section_header

    def create_config(self, _password: str):
        """Creates the default config file."""

        # Do this here so that ram is set correctly
        restart = self.restart_postgres_cmd

        # Creates the /etc/bgp directory
        self._create_config_dir()
        # Removes old conf section
        self._remove_old_config_section(self.section)
        # Gets ram on the machine
        _ram = int((virtual_memory().available / 1000 / 1000) * .9)
        logging.info(f"Setting ram to {_ram}")

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
            logging.debug(f"{os.path.split(self.path)[0]} exists, "
                          "not creating new directory")

    @classmethod    
    def _remove_old_config_section(cls, section: str):
        """Removes the old config file if it exists."""

        # Initialize ConfigParser
        _conf = SCP()
        # Read from .conf file
        _conf.read(cls.path)
        # Try to delete the section
        try:
            del _conf[section]
        # If it doesn' exist, doesn't matter
        except KeyError:
            return
        # Otherwise, write the change to the file
        with open(cls.path, "w+") as configfile:
            _conf.write(configfile)
        
    def _read_config(self, section: str, tag: str, raw: bool = False):
        """Reads the specified section from the configuration file."""

        for i in range(10):
            try:
                _parser = SCP()
                _parser.read(self.path)
                string = _parser.get(section, tag, raw=raw)
                try:
                    return int(string)
                except ValueError:
                    return string
            except configparser.ParsingError:
                logging.warning("Config parsing error. Potentially someone else edited config. Retrying")
                time.sleep(2)

    def get_db_creds(self, error=False) -> dict:
        """Returns database credentials from the config file."""

        try:
            # section = "bgp"
            subsections = ["user", "host", "database"]
            args = {x: self._read_config(self.section, x) for x in subsections}
            args["password"] = self._read_config(self.section,
                                                 "password",
                                                 raw=True)
            return args

        except NoSectionError:
            if error:
                raise NoSectionError
            self.install()
            return self.get_db_creds()

    def install(self) -> dict:
        """Installs the database section"""

        try:
            return self.get_db_creds(error=True)
        except Exception as e:#NoSectionError as e:
            # Database section is not installed, install it
            # Needed here due to circular imports
            from .postgres import Postgres
            Postgres(section=self.section).install(self.section)
            self.__init__(self.section)
            return self.get_db_creds()


    @property
    def ram(self) -> int:
        """Returns the amount of ram on a system."""

        return self._read_config(self.section, "ram")

    @property
    def restart_postgres_cmd(self) -> str:
        """Returns restart postgres cmd or writes it if none exists."""

        subsection = "restart_postgres_cmd"
        try:
            cmd = self._read_config(self.section, subsection)
        except NoSectionError:

            typical_cmd = "sudo systemctl restart postgresql@12-main.service"

            prompt = ("Enter the command to restart postgres\n"
                      f"Enter: {typical_cmd}\n"
                      "Custom: Enter cmd for your machine\n")
            # https://stackoverflow.com/a/58866220
            if "PYTEST_CURRENT_TEST" in os.environ:
                 return typical_cmd
            print(os.environ)
            cmd = input(prompt)
            if cmd == "":
                cmd = typical_cmd
        return cmd

    def _write_to_config(self, section, subsection, string):
        """Writes to a config file."""

        _conf = SCP()
        _conf.read(self.path)
        _conf[section][subsection] = str(string)
        with open(self.path, 'w') as configfile:
            _conf.write(configfile)
