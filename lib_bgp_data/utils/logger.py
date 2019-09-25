#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module used to contains helpful logging functions.

The Logger class used to be the logging class that was used. This class
sets a logging level for printing and for writing to a file. However,
it turns out that the logging module is insanely bad for multithreading.
So insane, that you cannot even import the dang thing without having it
deadlock on you. Crazy, I know. So therefore, I created another logging
class called Thread_Safe_Logger. This class basically emulates a logger
except that it only prints, and never writes to a file. It also never
deadlocks.

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
-Logger class is not used because logging deadlocks just on import
-Thread_Safe_Logger is used because it does not deadlock
-error_catcher is used so that functions fail nicely

Possible Future Improvements:
-Fix the error catcher
-Possibly use the Logger class to log all things in the API?
-Figure out how to use this class while multithreading
-Figure out how to exit nicely and not ruin my unit tests
"""

import re
import sys
import datetime
import os
import functools
import traceback
from enum import Enum
from functools import total_ordering
import pytest

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# compiled regex global to prevent unnessecary recompilation
tb_re = re.compile(r'''
                   .*?/lib_bgp_data
                   (?P<file_name>.*?.py)
                   .*?line.*?
                   (?P<line_num>\d+)
                   .*?in\s+
                   (?P<function>.*?)
                   \\n\s+
                   (?P<line>.+)
                   \\n
                   ''', re.VERBOSE | re.DOTALL
                   )


# This decorator wraps all funcs in a try except statement
# Note that it can only be put outside of funcs with self
# The point of the decorator is so code errors nicely with useful information
def error_catcher(msg=None):
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Gets traceback object and error information
                error_class, error_desc, tb = sys.exc_info()
                # Makes sure it's not a system exit call
                if not str(error_desc) == '1':
                    for msg in traceback.format_tb(tb):
                        self.logger.debug(msg)
                    # Gets last call from program
                    tb_to_re = [x for x in str(traceback.format_tb(tb))
                                .split("File") if "lib_bgp_data" in x][-1]
                    # Performs regex to capture useful information
                    capture = tb_re.search(tb_to_re)
                    # Formats error string nicely
                    err_str = ("\n{0}{1}{0}\n"
                               "      msg: {2}\n"
                               "      {3}: {4}\n"
                               "      file_name: {5}\n"
                               "      function:  {6}\n"
                               "      line #:    {7}\n"
                               "      line:      {8}\n"
                               "{0}______{0}\n"
                               ).format("_"*36,
                                        "ERROR!",
                                        msg,
                                        error_class,
                                        error_desc,
                                        capture.group("file_name"),
                                        capture.group("function"),
                                        capture.group("line_num"),
                                        capture.group("line"))
                    self.logger.error(err_str)
                    # hahaha so professional
                    print('\a')
                # Exit program and also kills all parents/ancestors
                if (hasattr(pytest, 'global_running_test')
                    and pytest.global_running_test):
                    raise e
                else:
                    sys.exit(1)  # Turning this on breaks pytest - figure it out
        return function_that_runs_func
    return my_decorator


class Logger:
    def __init__(self, args={}):
        """Initializes logger
        Logging levels are, in order:
        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG
        Anything equal to or higher than file_level will be appended to path
        Anything equal to or higher than stream_level will be printed
        """

        # Sets different logging properties
        self._set_properties(args)

        # Inits initial logger instance
        logger = self._init_logging(args)

        # Adds file handler to logger
        self._init_file_handler(logger, args)

        # Adds stream handler if not child
        self._init_stream_handler(logger, args)

        self.logger = logger

    def _set_properties(self, args):
        """Inits different logging properties"""

        # Import done here so as not to overwrite my enum
        import logging

        # Sets variables if args is not set
        log_name = args.get("log_name")
        if log_name is None:
            log_name = "lib_bgp_data.log"

        self.file_level = args.get("file_level")
        if self.file_level is None:
            self.file_level = logging.WARNING

        self.stream_level = args.get("stream_level")
        if self.stream_level is None:
            self.stream_level = logging.INFO

        log_dir = args.get("log_dir")
        if log_dir is None:
            log_dir = "/var/log/lib_bgp_data"
        self._make_dir(log_dir)

        prepend = args.get("prepend")
        if prepend is None:
            prepend = datetime.datetime.now().strftime("%Y_%m_%d_%I_%M%S")

        self.log_name = "{}_{}".format(prepend, log_name)

    def _make_dir(self, path):
        """Initializes a directory"""

        if not os.path.exists(path):
            os.makedirs(path)
        self.log_dir = path

    def _init_logging(self, args):
        """Initializes the initial logger"""

        # Import done here so as not to overwrite my enum
        import logging

        # Initialize logging
        logger = logging.getLogger(__name__)
        if logger.hasHandlers() and args.get("is_child") is None:
            logger.handlers.clear()
        # Must use multiprocessing logger to avoid locking
        # logger = multiprocessing.get_logger()
        logger.setLevel(logging.DEBUG)
        return logger

    def _init_file_handler(self, logger, args):
        """Initializes file handler for logging"""

        # Import done here so as not to overwrite my enum
        import logging

        # Initialize File Handler
        self.file_path = os.path.join(self.log_dir, self.log_name)
        self.file_handler = logging.FileHandler(self.file_path)
        self.file_handler.setLevel(self.file_level)
        file_handler_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        self.file_handler.setFormatter(file_handler_formatter)
        logger.addHandler(self.file_handler)

    def _init_stream_handler(self, logger, args):
        """Adds stream handler while avoiding multithreading problems"""

        # Import done here so as not to overwrite my enum
        import logging

        if args.get("is_child") is None:
            # Initialize Stream Handler
            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setLevel(self.stream_level)
            stream_handler_formatter = logging.Formatter(
                '%(levelname)s - %(name)s - %(message)s')
            self.stream_handler.setFormatter(stream_handler_formatter)
            logger.addHandler(self.stream_handler)
            # Must be done or else:
            # https://stackoverflow.com/questions/21127360/
            logger.propogate = False
        else:
            logger.propogate = True


@total_ordering
class logging(Enum):
    """Replacement for the logging class"""

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


class Thread_Safe_Logger:
    """Logger class for process safe logging, explained below

    Because the logging module deadlocks when used with lots of multiprocessing
    I have taken it out and replaced it with something simpler. Logging
    to files are awesome, but clearly python logging sucks when using
    multiprocessing, I cannot even import logging without it somehow
    deadlocking so I will be using my own crap class from now on.
    """

    def __init__(self, args={}):
        """Initializes logger
        Logging levels are, in order:
        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG
        """

        stream_level = args.get("stream_level")
        # Sets stream level
        stream_level = int(stream_level) if stream_level else logging.INFO
        self.level = stream_level
        # Sets all the standard logging functions
        levels = ["notset", "debug", "info", "warning", "error", "critical"]
        # Makes log functions
        log_funcs = [self._make_log_func(stream_level, x) for x in logging]
        # Sets log functions
        [setattr(self, x, y) for x, y in zip(levels, log_funcs)]

    def _make_log_func(self, stream_level, log_level):
        """Dynamically creates functions that emulate normal logging funcs"""

        def _function(msg):
            """Function that is created"""

            # If the stream level is less than or equal to the log level
            if stream_level <= log_level:
                # Print the message
                print("{}: {}".format(datetime.datetime.now(), msg))
                # Flush the output for multithreading
                sys.stdout.flush()
        return _function
