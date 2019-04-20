#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Logger with logging functionality
This module contains a logging class that impliments logging.
Because the logging module deadlocks when used with lots of multiprocessing
I have decided to take it out and replace it with something simpler. Logging
to files are awesome, but clearly python logging sucks when using
multiprocessing, I cannot even import logging without it somehow deadlocking
so I will be using my own crap class from now on
"""

import re
import sys
import datetime
import functools
import traceback
from enum import Enum
from functools import total_ordering

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@total_ordering
class logging(Enum):
    """Replacement for the logging class, explained above"""

    # Defines order for the iterator
    __order__ = "NOTSET DEBUG INFO WARNING ERROR CRITICAL"
    # Defines enum attributes
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __lt__(self, other):
        """Comparitor for the logging levels"""

        return self.value < other


class Logger:
    """Logger class for process safe logging, explained at module header"""

    def __init__(self, args):
        """Initializes logger
        Logging levels are, in order:
        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG
        Anything equal to or higher than file_level will be appended to path
        Anything equal to or higher than stream_level will be printed
        Explanation for the logger class at top of module, in short this
        class works with multiprocessing
        """

        stream_level = args.get("stream_level")
        # Sets stream level
        stream_level = int(stream_level) if stream_level else logging.INFO
        # Sets all the standard logging functions
        levels = ["notset", "debug", "info", "warning", "error", "critical"]
        # Makes log functions
        log_funcs = [self._make_log_func(stream_level, x) for x in logging]
        # Sets log functions
        [setattr(self, x, y) for x, y in zip(levels, log_funcs)]

    def _make_log_func(self, stream_level, log_level):
        """Dynamically creates functions"""

        def _function(msg):
            """Function that is created"""

            # If the stream level is less than or equal to the log level
            if stream_level <= log_level:
                # Print the message
                print("{}: {}".format(datetime.datetime.now(), msg))
                # Flush the output for multithreading
                sys.stdout.flush()
        return _function
