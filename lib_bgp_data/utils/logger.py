#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module used to contains helpful logging functions.

The Logger class used to be the logging class that was used. This class
sets a logging level for printing and for writing to a file. However,
it turns out that the logging module is insanely bad for multithreading.

There is also a nice decorator called error_catcher. The point of this
was supposed to be to catch any errors that occur and fail nicely with
good debug statements, which is especially useful when multithreading.
However with unit testing, it needs to be able fail really horribly,
so that has become disabled as well. Still, eventually it will be
fixed, so all functions that have self should be contained within the
error catcher.

For an explanation on how logging works:
logging has different levels. If you are below the set logging level,
nothing gets recorded. The levels are, in order top to bottom:

        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG
        logging.NOTSET

Design Choices:
-error_catcher is used so that functions fail nicely

Possible Future Improvements:
-Fix the error catcher
-Possibly use the Logger class to log all things in the API?
-Figure out how to use this class while multithreading
-Figure out how to exit nicely and not ruin my unit tests
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from datetime import datetime
import logging
import os

import multiprocessing_logging

from .config import set_global_section_header

def config_logging(level=logging.INFO, section=None):
    """Configures logging to log to a file"""

    try:
        from .config import global_section_header
    except ImportError:
        global_section_header = set_global_section_header(section)

    # Makes log path and returns it
    path = _get_log_path(global_section_header)
    if len(logging.root.handlers) != 2:
        logging.root.handlers = []
        logging.basicConfig(level=level,
                            format='%(asctime)s-%(levelname)s: %(message)s',
                            handlers=[logging.FileHandler(path),
                                      logging.StreamHandler()])

        logging.captureWarnings(True)
        multiprocessing_logging.install_mp_handler()

def _get_log_path(section):
    fname = f"{section}_{datetime.now().strftime('%Y_%M_%d')}.log"
    log_dir = f"/var/log/lib_bgp_data/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, fname)
