#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Logger with logging functionality"""

import re
import sys
import datetime
import multiprocessing
import logging
import os
import functools
import traceback

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


#compiled regex global to prevent unnessecary recompilation
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
            except:
                # Gets traceback object and error information
                error_class, error_desc, tb = sys.exc_info()
                # Makes sure it's not a system exit call
                if not str(error_desc) == '1':
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
                    print('\a')
                # Exit program and also kills all parents/ancestors
                sys.exit(1)
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

        # Sets variables if args is not set
        log_name = args.get("log_name")
        if log_name is None:
            log_name = "lib_bgp_data.log"

        file_level = args.get("file_level")
        if file_level is None:
            file_level = logging.WARNING

        stream_level = args.get("stream_level")
        if stream_level is None:
            stream_level = logging.INFO

        log_dir = args.get("log_dir")
        if log_dir is None:
            log_dir = "/var/log/lib_bgp_data"
        self._make_dir(log_dir)

        prepend = args.get("prepend")
        if prepend is None:
            prepend = datetime.datetime.now().strftime("%Y_%m_%d_%I_%M%S")

        self.log_name = "{}_{}".format(prepend, log_name)

        # Initialize logging
        logger = logging.getLogger(__name__)
        if logger.hasHandlers() and args.get("ancestor") is None:
            logger.handlers.clear()
        # Must use multiprocessing logger to avoid locking
        # logger = multiprocessing.get_logger()
        logger.setLevel(logging.DEBUG)

        # Initialize File Handler
        self.file_path = os.path.join(log_dir, self.log_name)
        self.file_handler = logging.FileHandler(self.file_path)
        self.file_handler.setLevel(file_level)
        file_handler_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        self.file_handler.setFormatter(file_handler_formatter)
        logger.addHandler(self.file_handler)

        if args.get("ancestor") is None:
            # Initialize Stream Handler
            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setLevel(stream_level)
            stream_handler_formatter = logging.Formatter(
                '%(levelname)s - %(name)s - %(message)s')
            self.stream_handler.setFormatter(stream_handler_formatter)
            logger.addHandler(self.stream_handler)
            # Must be done or else:
            # https://stackoverflow.com/questions/21127360/python-2-7-log-displayed-twice-when-logging-module-is-used-in-two-python-scri?noredirect=1&lq=1
            logger.propogate = False
        else:
            logger.propogate = True
        self.logger = logger

    def _make_dir(self, path):
        """Initializes a directory"""

        if not os.path.exists(path):
            os.makedirs(path)
