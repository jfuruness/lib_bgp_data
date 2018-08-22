#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Config that can parse a config file"""

__author__ = "Justin Furuness"

from configparser import SafeConfigParser as SCP


class Config:
    """Interact with config file"""

    def __init__(self, logger, path='/etc/bgp/bgp.conf'):
        """Initializes path for config file"""

        self.path = path
        self.logger = logger

    def read_config(self, section, tag, raw=False):
        """Reads the specified section from the configuration file"""

        parser = SCP()
        parser.read(self.path)
        return parser.get(section, tag, raw=raw)

    def get_db_creds(self):
        """Returns database credentials from the config file"""
        
        try:
            section = "bgp"
            username = self.read_config(section, "username")
            password = self.read_config(section, "password", raw=True)
            host = self.read_config(section, "host")
            database = self.read_config(section, "database")
            return username, password, host, database
        except Exception as e:
            self.logger.error("Problem parsing config file: {}".format(e))
