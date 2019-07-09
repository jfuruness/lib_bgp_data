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
from .split_validity_sql import split_validity_table_sql
from .sql_queries import all_sql_queries

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

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

    __slots__ = ['path', 'csv_dir', 'logger']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)
        

    @error_catcher()
    def run_policies(self):
        """Downloads and stores roas from a json"""

        self.run_rov_policy()
        self.run_simple_time_heuristic()

    def run_rov_policy(self):
        for sql in split_validity_table_sql + all_sql_queries:
            self.cursor.execute(sql)

    @error_catcher()
    def run_simple_time_heuristic(self):
        """Makes policy decision based on age of announcements

        For more in depth explanation, read README"""

        pass
