#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains rpki validator to perform validation

The ripe validator first starts up. Then all the prefix and origin
pairs are uniquely """

import http.server
import socketserver
from multiprocess import Process
import functools
from contextlib import contextmanager
import os
from subprocess import Popen, PIPE
import time
import urllib
from ..utils import utils, error_catcher, Thread_Safe_Logger as Logger
from .tables import Unique_Prefix_Origins_Table, Validity_Table
from ..utils import Database, db_connection

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@contextmanager
def _serve_file(self, path):
    """Serves a file on a separate process, and kills it when done"""

    p = Process(target=self._serve_file, args=(path, ))
    p.start()
    yield 
    p.terminate()
    p.join()

@contextmanager
def _run_rpki_validator(self, file_path, rpki_path):
    """Runs the ripe validator in a subprocess call and closes it correctly"""

    # Serves the ripe file
    with _serve_file(self, file_path):
        # Subprocess
        self.logger.info("About to run rpki validator")
        # Because the output of the rpki validator is garbage we omit it
        process = Popen([rpki_path], stdout=PIPE, stderr=PIPE)
#        stdout, stderr = process.communicate()
#        self.logger.debug(stdout)
#        self.logger.debug(stderr)
        self.logger.info("Running rpki validator")
        yield 
        process.terminate()
        self.logger.info("Closed rpki validator")


class RPKI_Validator:
    """This class gets validity data from ripe""" 

    __slots__ = ['path', 'csv_dir', 'args', 'logger', 'csv_path', 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)
        

    @error_catcher()
    @utils.run_parser()
    def run_validator(self):
        """Downloads and stores roas from a json"""

        # Writes the file that the validator uses for validation
        validator_file, total_rows = self._write_validator_file()
        rpki_path = ("/mnt/dbstorage/validator/dev/"
                     "rpki-validator-3.0-DEV20180902182639/"
                     "rpki-validator-3.sh")
        # This runs the rpki validator
        with _run_rpki_validator(self, validator_file, rpki_path):
            # First we wait for the validator to load the data
            self._wait_for_validator_load(total_rows)
            # Writes validator to database
            with db_connection(Validity_Table, self.logger) as v_table:
                v_table.execute("DROP TABLE IF EXISTS validity;")
            utils.rows_to_db(self.logger,
                             self._get_ripe_data(),
                             "{}/validity.csv".format(self.csv_dir),  #  CSV 
                             Validity_Table)
        utils.delete_paths(self.logger, [validator_file, "/tmp/validator.csv"])
        with db_connection(Validity_Table, self.logger) as v_table:
            v_table.split_table()

########################
### Helper Functions ###
########################

    @error_catcher()
    def _write_validator_file(self, path="/tmp/validator.csv"):
        """Writes validator file

        This function write the validator file by taking the mrt announcements
        getting all unique prefix origin pairs, and writing it all to a .gz
        for Ripes RPKI validator to use
        """

        # Initializes a prefix origin table
        with db_connection(Unique_Prefix_Origins_Table, self.logger) as table:
            # Generates a unique prefix origin table for ripe
            # Gets the unique prefix origins from the mrt announcements
            # And write them to a table with the default placeholder of 100
            # For easy integration with rpki validator
            table.fill_table()
            rpki_path = ("/validator/dev/"
                         "rpki-validator-3.0-DEV20180902182639/"
                         "rpki-validator-3.sh")
            # This writes the validator file that the rpki validator will use
            # And returns the file path and the total rows of the file
            return table.write_validator_file(path=path)

    @error_catcher()
    def _get_ripe_data(self):
        """Gets the data from ripe and formats it for csv insertions"""

        self.logger.info("Getting data from ripe")
        # Then we get the data from the ripe RPKI validator
        # Todo for later, change 10mil to be total count
        url = "http://localhost:8080/api/bgp/?pageSize=10000000"
        # Gets a list of dictionaries of asns
        asns = utils.get_json(url, self._get_headers())["data"]
        # Changes the validation states to numbers and returns them
        return [self._format_asn_dict(x) for x in asns]

    
    @error_catcher()
    def _format_asn_dict(self, asn):
        """Formats json objects for csv rows"""

        valid = {"VALID": 1,
                 "UNKNOWN": 0,
                 "INVALID_LENGTH": -1,
                 "INVALID_ASN": -2}
        return [int(asn["asn"][2:]), asn["prefix"], valid.get(asn["validity"])]

    @error_catcher()
    def _get_row_count(self, headers):
        """Returns row count of json object for waiting"""

        try:
            return utils.get_json("http://localhost:8080/api/bgp/", headers)["metadata"]["totalCount"]
        except Exception as e:
            self.logger.debug("Problem with getting json: {}".format(e))
            return 0

    def _serve_file(self, path):
        """Makes a simple http server and serves a file"""

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        os.chdir("/tmp/")
        socketserver.TCPServer(("", 8000), Handler).serve_forever()

    def _wait_for_validator_load(self, total_rows):
        """Waits for the rpki validator to load all of it's data"""

        time.sleep(30)
        while self._get_row_count(self._get_headers()) < total_rows:
            self.logger.info("Waiting for validator load")
            self.logger.debug(total_rows)
            self.logger.debug(self._get_row_count(self._get_headers()))
            time.sleep(30)


    @error_catcher()
    def _get_headers(self):
        """Returns the proper connection for the requests module"""

        return {"Connection": "keep-alive",
                   "Cache-Control": "max-age=0",
                   "Upgrade-Insecure-Requests": 1,
                   "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64)"
                                  " AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/73.0.3683.86 Safari/537.36"),
                    "Accept": ("text/html,application/xhtml+xml,"
                               "application/xml;q=0.9,image/webp,"
                               "image/apng,*/*;q=0.8,"
                               "application/signed-exchange;v=b3"),
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9"}
