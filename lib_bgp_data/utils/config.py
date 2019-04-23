#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Config that can parse a config file"""

import os
from configparser import ConfigParser as SCP
from .logger import error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Config:
    """Interact with config file"""

    __slots__ = ["path", "logger"]

    @error_catcher()
    def __init__(self, logger, path="/etc/bgp/bgp.conf"):
        """Initializes path for config file"""

        self.path = path
        self.logger = logger
        # If config does not exist, create one
        if not os.path.isfile(self.path):
            self._create_config()

    def _create_config(self):
        """Creates a blank config file"""

        config = SCP()
        config["bgp"] = {"user": "Not Initialized",
                         "host": "Not Initialized",
                         "database": "Not Initialized",
                         "last_relationship_update": "0"
                         }
        with open(self.path, "w") as config_file:
            config.write(config_file)

    @error_catcher()
    def _read_config(self, section, tag, raw=False):
        """Reads the specified section from the configuration file"""

        parser = SCP()
        parser.read(self.path)
        string = parser.get(section, tag, raw=raw)
        try:
            return int(string)
#        except SCP.NoSectionError:
#            self._create_config()
        except:
            return string

    @error_catcher()
    def get_db_creds(self):
        """Returns database credentials from the config file"""

        section = "bgp"
        subsections = ["user", "host", "database"]
        args = {x: self._read_config(section, x) for x in subsections}
        args["password"] = self._read_config(section, "password", raw=True)
        return args

    @property
    def last_date(self):
        """Returns the last date relationship files where parsed from the config file"""

        section  = "bgp"
        subsection = "last_relationship_update"
        last_date = self._read_config(section, subsection)
        if last_date is None:
            return 0
        else:
            return int(last_date)
        
    @error_catcher()
    def update_last_date(self, _date):
        """Edits the last date parsed in the config file"""

        self._write_to_config("bgp", "last_relationship_update", _date)

    def _write_to_config(self, section, subsection, string):
        """Writes to a config file"""

        conf = SCP()
        conf.read(self.path)
        conf[section][subsection] = str(string)
        with open(self.path, 'w') as configfile:
            conf.write(configfile) 
