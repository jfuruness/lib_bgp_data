#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Config that creates and parses a config.

To see the config itself, see the create_config function and view the
_config dictionary.
"""

import os
from configparser import ConfigParser as SCP
from configparser import NoSectionError
from psutil import virtual_memory
from .logger import error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Config:
    """Interact with config file"""

    __slots__ = ["path", "logger"]

    @error_catcher()
    def __init__(self, logger, path="/etc/bgp/bgp.conf"):
        """Initializes path for config file."""

        self.path = path
        self.logger = logger

    def create_config(self, _password):
        """Creates the default config file."""

        # Creates the /etc/bgp directory
        self._create_config_dir()
        # Removes old conf
        self._remove_old_config()

        # Gets ram on the machine
        _ram = int((virtual_memory().available/1000/1000)*.9)
        self.logger.info("Setting ram to {}".format(_ram))

        # Conf info
        _config = SCP()
        _config["bgp"] = {"host": "localhost",
                          "database": "bgp",
                          "password": _password,
                          "user": "bgp_user",
                          "last_relationship_update": "0",
                          "ram": _ram,
                          "restart_postgres_cmd": self.restart_postgres_cmd}

        # Writes the config
        with open(self.path, "w+") as config_file:
            _config.write(config_file)

    @error_catcher()
    def _create_config_dir(self):
        """Creates the /etc/bgp directory."""

        try:
            os.makedirs(os.path.split(self.path)[0])
        except FileExistsError:
            self.logger.debug("About to overwrite {}".format(
                os.path.split(self.path)[0]))

    @error_catcher()
    def _remove_old_config(self):
        """Removes the old config file if it exists."""

        # Supposedly try except is more pythonic than if then so yah whatever
        # This looks wicked dumb though
        # Removes the old config if exists
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def _read_config(self, section, tag, raw=False):
        """Reads the specified section from the configuration file."""

        parser = SCP()
        parser.read(self.path)
        string = parser.get(section, tag, raw=raw)
        try:
            return int(string)
        except ValueError:
            return string

    @error_catcher()
    def get_db_creds(self):
        """Returns database credentials from the config file."""

        section = "bgp"
        subsections = ["user", "host", "database"]
        args = {x: self._read_config(section, x) for x in subsections}
        args["password"] = self._read_config(section, "password", raw=True)
        return args

    @property
    def last_date(self):
        """Returns the last date relationship files where parsed."""

        section = "bgp"
        subsection = "last_relationship_update"
        return int(self._read_config(section, subsection))

    @property
    def ram(self):
        """Returns the amount of ram on a system."""

        return self._read_config("bgp", "ram")

    @property
    def restart_postgres_cmd(self):
        """Returns restart postgres cmd or writes it if none exists."""

        section = "bgp"
        subsection = "restart_postgres_cmd"
        try:
            cmd = self._read_config(section, subsection)
        except NoSectionError:
            prompt = "Enter the command to restart postgres\n"
            prompt += "0 or Enter: "
            prompt += "sudo systemctl restart postgresql@11-main.service\n"
            prompt += "1: sudo systemctl restart postgresql: \n"
            prompt += "Custom: Enter cmd for your machine\n"
            cmd = input(prompt)
            if cmd == "" or "0":
                cmd = "sudo systemctl restart postgresql@11-main.service"
            elif cmd == "1":
                cmd = "sudo systemctl restart postgresql"
        return cmd

    @error_catcher()
    def update_last_date(self, date):
        """Edits the last date parsed in the config file."""

        self._write_to_config("bgp", "last_relationship_update", date)

    def _write_to_config(self, section, subsection, string):
        """Writes to a config file."""

        _conf = SCP()
        _conf.read(self.path)
        _conf[section][subsection] = str(string)
        with open(self.path, 'w') as configfile:
            _conf.write(configfile)
