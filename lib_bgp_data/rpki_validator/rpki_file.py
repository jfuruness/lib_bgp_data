#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class RPKI_File

The purpose of this class is to write a file of all announcements that
the RPKI Validator will then use as input to determine the validity.

For a more in depth explanation see README.
"""

import logging
import os
import time

import gzip
import http.server
from pathos.multiprocessing import ProcessingPool
from psutil import process_iter
from signal import SIGTERM
import socketserver
import urllib

from .tables import Unique_Prefix_Origins_Table
from ..utils import utils

__authors__ = ["Justin Furuness", "Cameron Morris"]
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class RPKI_File:
    """This class gets validity data from ripe"""

    __slots__ = ["path", "total_lines", "_process"]

    _dir = "/tmp/"
    hosted_name = "upo_csv_path.csv.gz"
    port = 8000

    def __init__(self, table_input):
        """Downloads and stores roas from a json"""

        self.path = self._dir + self.hosted_name.replace(".gz", "")
        with Unique_Prefix_Origins_Table(clear=True) as _db:
            _db.fill_table(table_input)
            _db.copy_table(self.path)
            self.total_lines = utils.get_lines_in_file(self.path)
            self._gzip_file()

#################################
### Context Manager Functions ###
#################################

    def __enter__(self):
        """What to do when the context manager is called on this class

        Starts the process for serving the file"""

        self.spawn_process()
        return self


    def __exit__(self, type, value, traceback):
        """Closes the file process"""

        self.close()

############################
### Serve File Functions ###
############################

    def spawn_process(self):
        """Spawns file serving process"""

        self._process = ProcessingPool()
        self._process.apipe(self._serve_file)
        logging.debug("Served RPKI File")

    def close(self):
        """Closes file process"""

        self._process.close()
        self._process.terminate()
        self._process.join()
        self._process.clear()
        utils.delete_paths(RPKI_File.hosted_name)
        logging.debug("Closed RPKI File")
        
########################
### Helper Functions ###
########################

    def _gzip_file(self):
        """gzips the file for proper formatting in rpki validator"""

        with open(self.path, 'rb') as f_in, gzip.open(
            os.path.join(self._dir,
                         self.hosted_name), 'wb') as f_out:

            f_out.writelines(f_in)

        utils.delete_paths(self.path)

    def _serve_file(self):
        """Makes a simple http server and serves a file in /tmp"""

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        # Changes directory to be in /tmp
        os.chdir(self._dir)
        # Serve the file on port 8000
        socketserver.TCPServer(("", RPKI_File.port), Handler).serve_forever()
