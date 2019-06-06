#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains What_if_analsyis to run policies on mrt_announcements"""

import http.server
import socketserver
from multiprocess import Process
import functools
from contextlib import contextmanager
import os
from subprocess import Popen
import time
import urllib
from ..utils import utils, Thread_Safe_Logger as Logger, error_catcher, Database
from .tables import Unique_Prefix_Origins_Table, Validity_Table

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

# This decorator wraps any run policy function to write to a csv and db insert
# This starts the run policy, cleans all paths, ends the parser, and records time
# The point of this decorator is to make sure the policy runs smoothly
def run_policy():
    def my_decorator(run_policy_func):
        @functools.wraps(run_policy_func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator

            # Gets the start time
            start_time = utils.now()
            # Deletes everything from and creates paths
            utils.clean_paths(self.logger, self.all_files)
            try:
                # Runs the parser
                rows, csv_path, table = run_policy_func(self, *args, **kwargs)
                utils.write_csv(self.logger, rows, csv_path)
                utils.csv_to_db(self.logger, table, csv_path)

            # Upon error, log the exception
            except Exception as e:
                self.logger.error(e)
                raise e
            # End the parser to delete all files and directories always
            finally:
                # Clean up don't be messy yo
                utils.end_parser(self.logger, self.all_files, start_time)
        return function_that_runs_func
    return my_decorator

@contextmanager
def _serve_file(self, path):
    p = Process(target=self._serve_file, args=(path, ))
    p.start()
    yield 
    p.terminate()
    p.join()

@contextmanager
def _run_rpki_validator(self, file_path, rpki_path):
    with _serve_file(self, file_path):
        process = Popen([rpki_path])
        yield 
        process.terminate()

#TODO Add to docs valid=1, unknown=0, invalid=-1


class What_If_Analysis:
    """This class runs all the policies on the mrt_announcements table""" 

    __slots__ = ['path', 'csv_dir', 'args', 'logger', 'csv_path', 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)
        

    @error_catcher()
    @utils.run_parser()
    def run_policies(self, db=True):
        """Downloads and stores roas from a json"""

        self.run_rov_policy()
        self.run_time_policy()

    @error_catcher()
    @run_policy()
    def run_simple_time_heuristic(self):
        """Makes policy decision based on age of announcements

        For more in depth explanation, read README"""

        pass
        # I have the sql version of this code somewhere, it is a simple join

        return rows, csv_path, table
