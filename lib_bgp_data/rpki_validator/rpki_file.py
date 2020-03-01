#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class RPKI_File

The purpose of this class is to write a file of all announcements that
the RPKI Validator will then use as input to determine the validity.

For a more in depth explanation see README.

1. Write the validator file.
    -Handled in the _write_validator_file function
    -Normally the RPKI Validator pulls all prefix origin pairs from the
     nternet, but those will not match old datasets
    -Instead, our own validator file is written
2. Host validator file
    -Handled in _serve_file decorator
    -Again, this is a file of all prefix origin pairs from our MRT
     announcements table

Design choices (summarizing from above):
    -We serve our own file for the RPKI Validator to be able to use
     old prefix origin pairs
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files

Possible Future Extensions:
    -Add test cases
    -Reduce total information in the headers
"""


from multiprocess import Process
import os
from subprocess import Popen, PIPE, check_call, DEVNULL
import time

import http.server
from psutil import process_iter
from signal import SIGTERM
import socketserver
import urllib


from .tables import Unique_Prefix_Origins_Table
from ..utils import utils

__authors__ = ["Justin Furuness", "Cameron Morris"]
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class RPKI_File:
    """This class gets validity data from ripe"""

    __slots__ = ["path", "total_lines", "port", "_dir", "hosted_name", "port",
                 "_process"]

    _dir = "/tmp/"
    hosted_name = "upo_csv_path.csv.gz"
    port = 8000

    def __init__(self):
        """Downloads and stores roas from a json"""

        self.path = "/tmp/unique_prefix_origins.csv"
        with Unique_Prefix_Origins_Table(self.logger, clear=True) as _db:
            _db.fill_table()
            _db.copy_table(self.path)
            self.total_lines = utils.get_lines(self.path)
            self._gzip_file()

#################################
### Context Manager Functions ###
#################################

    def __enter__(self):
        """What to do when the context manager is called on this class

        Starts the process for serving the file"""

        self._process = Process(target=self._serve_file)
        self._process.start()
        self.logger.debug(f"Serving file")
        return self

    def __exit__(self, type, value, traceback):
        self._process.terminate()
        self._process.join()
        utils.delete_paths[RPKI_File.hosted_name]
        return True
        
########################
### Helper Functions ###
########################

    def _gzip_file(self):
        """gzips the file for proper formatting in rpki validator"""

        with open(self.path, 'rb') as f_in, gzip.open(
            os.path.join(self._dir,
                         self.file_name, 'wb') as f_out:

            f_out.write_lines(f_in)

        utils.delete_paths(self.logger, self.path)

    def _serve_file(self):
        """Makes a simple http server and serves a file in /tmp"""

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        # Changes directory to be in /tmp
        os.chdir(self._dir)
        # Serve the file on port 8000
        socketserver.TCPServer(("", self.port), Handler).serve_forever()
