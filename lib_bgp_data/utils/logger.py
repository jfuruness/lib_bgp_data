#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module used to contains helpful logging functions"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from datetime import datetime
import logging
import os

import multiprocessing_logging

from ..database.config import set_global_section_header


def config_logging(level=logging.INFO, section=None, reconfigure=False):
    """Configures logging to log to a file"""


    if len(logging.root.handlers) != 2 or reconfigure:
        try:
            from ..database.config import global_section_header
        except ImportError:
            global_section_header = set_global_section_header(section)
    
        # Makes log path and returns it
        path = _get_log_path(global_section_header)
        logging.root.handlers = []
        logging.basicConfig(level=level,
                            format='%(asctime)s-%(levelname)s: %(message)s',
                            handlers=[logging.FileHandler(path),
                                      logging.StreamHandler()])

        logging.captureWarnings(True)
        multiprocessing_logging.install_mp_handler()
        logging.debug("initialized logger")


def _get_log_path(section):
    fname = f"{section}_{datetime.now().strftime('%Y_%m_%d')}.log"
    log_dir = "/var/log/lib_bgp_data/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, fname)
