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
from ..logger import Logger, error_catcher
from .. import utils
from .tables import Unique_Prefix_Origins_Table

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

class What_if_Analysis:
    """This class runs all the policies on the mrt_announcements table""" 

    __slots__ = ['path', 'csv_dir', 'args', 'logger', 'csv_path', 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args, "What If Analysis")
        

    @error_catcher()
    @utils.run_parser()
    def run_policies(self, db=True):
        """Downloads and stores roas from a json"""

        unique_p_o = Unique_Prefix_Origins_Table(self.logger)
        unique_p_o.fill_table()
        rpki_path = "/justins_validator/rpki-validator-3.0-397/rpki-validator-3.sh"
        new_path, total_rows = unique_p_o.write_validator_file(path="/tmp/validator.csv")
        new_path = "/tmp/validator.csv.gz"
        total_rows = 936818
        with _run_rpki_validator(self, new_path, rpki_path):
            while self._get_row_count() < total_rows:
                print(total_rows)
                print(self._get_row_count())
                time.sleep(5) 
        # Query the json and make a table from it
        # make an index like the one on hijack
        # do sql queries in word doc for policy4


        # Delete table
        # delete csv and gz files



#        self.run_simple_time_heuristic()
#        self.run_enforce_invalid_asn_only()
#        self.run_enforce_invalid_length_only()
#        self.run_enfore_invalid()
#        self.run_pass_if_no_alternative()
#        self.run_pass_if_no_alternative_including_superprefixes()

    @error_catcher()
    def _get_row_count(self):
        """Returns row count of json object for waiting"""

        try:
            return 0
            return utils.get_json("http://localhost:8080/api/bgp")["metadata"]["total_count"]
        except Exception as e:
            self.logger.warning("Problem with getting json: {}".format(e))
            return 0

    @error_catcher()
    @run_policy()
    def run_simple_time_heuristic(self):
        """Makes policy decision based on age of announcements

        For more in depth explanation, read README"""

        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_enforce_invalid_asn_only(self):
        """Makes policy decision based on validity of asn

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_enforce_invalid_length_only(self):
        """Makes policy decision based on validity of length

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_enfore_invalid(self):
        """Makes policy decision based on validity of length or asn

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_pass_if_no_alternative(self):
        """Allows announcement only if no alternative exists

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_pass_if_no_alternative_including_superprefixes(self):
        """Allows anouncement if no alternative/superprefix exists

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

########################
### Helper Functions ###
########################

    def _serve_file(self, path):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        os.chdir("/tmp/")
        socketserver.TCPServer(("", 8000), Handler).serve_forever()

    def _gzip_file(self, path):
        """Gzips the validator.txt file"""

        with open(path, 'rb') as f_in, gzip.open('{}.gz'.format(path), 'wb') as f_out:
            f_out.writelines(f_in)
