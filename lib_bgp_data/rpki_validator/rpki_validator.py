#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class RPKI_Validator

The purpose of this class is to obtain the validity data for all of the
prefix origin pairs in our announcements data, and insert it into a
database. This is done through a series of steps.

1. Write the validator file.
    -Handled in the _write_validator_file function
    -Normally the RPKI Validator pulls all prefix origin pairs from the
     internet, but those will not match old datasets
    -Instead, our own validator file is written
2. Host validator file
    -Handled in _serve_file decorator
    -Again, this is a file of all prefix origin pairs from our MRT
     announcements table
3. Run the RPKI Validator
    -Handled in run_validator function
4. Wait for the RPKI Validator to load the whole file
    -Handled in the _wait_for_validator_load function
    -This usually takes about 10 minutes
5. Get the json for the prefix origin pairs and their validity
    -Handled in the _get_ripe_data function
    -Need to query IPV6 port because that's what it runs on
6. Convert all strings to int's
    -Handled in the format_asn function
    -Done to save space and time when joining with later tables
7. Parsed information is stored in csv files, and old files are deleted
    -CSVs are chosen over binaries even though they are slightly slower
        -CSVs are more portable and don't rely on postgres versions
        -Binary file insertion relies on specific postgres instance
    -Old files are deleted to free up space
8. CSV files are inserted into postgres using COPY, and then deleted
    -COPY is used for speedy bulk insertions
    -Files are deleted to save space

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
    -Move the file serving functions into their own class
        -Improves readability?
    -Add test cases
    -Reduce total information in the headers
"""

import http.server
import socketserver
from multiprocess import Process
from contextlib import contextmanager
import os
from subprocess import Popen, PIPE, check_call
import time
from ..utils import utils, error_catcher
from .tables import Unique_Prefix_Origins_Table, ROV_Validity_Table
from ..utils import db_connection

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@contextmanager
def _serve_file(self, path):
    """Serves a file on a separate process, and kills it when done."""

    p = Process(target=self._serve_file, args=(path, ))
    p.start()
    self.logger.debug("Serving file at {}".format(path))
    yield
    p.terminate()
    p.join()


@contextmanager
def _run_rpki_validator(self, file_path, rpki_path):
    """Runs the RPKI validator in a subprocess call.

    Once finished the validator is closed correctly."""

    self.logger.info("Make way for the rpki validator!!!")
    self.logger.info("Killing all port 8080 processes, cause idc")
    check_call("sudo kill -9 $(lsof -t -i:8080)", shell=True)

    # Must remove these to ensure a clean run
    utils.clean_paths(self.logger, self.rpki_db_paths)


    # Serves the ripe file
    with _serve_file(self, file_path):
        # Subprocess
        self.logger.info("About to run rpki validator")
        # Because the output of the rpki validator is garbage we omit it
        # Unless we are in debug mode
        if self.logger.level < 20:  # Info
            process = Popen([rpki_path])
        else:
            process = Popen([rpki_path], stdout=PIPE, stderr=PIPE)
        self.logger.debug("Running rpki validator")
        yield
        process.terminate()
        self.logger.debug("Closed rpki validator")


class RPKI_Validator:
    """This class gets validity data from ripe"""

    __slots__ = ['path', 'csv_dir', 'logger', 'rpki_path', 'upo_csv_path',
                 'rpki_db_paths']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)
        rpki_package_path = "/var/lib/rpki-validator-3/"
        self.rpki_path = rpki_package_path + "rpki-validator-3.sh"
        self.rpki_db_paths = [rpki_package_path + x for x in ["db/", "rsync/"]]
        self.upo_csv_path = "/tmp/upo_csv_path.csv"

    @error_catcher()
    @utils.run_parser()
    def run_validator(self):
        """Downloads and stores roas from a json"""

        # Writes the file that the validator uses for validation
        validator_file, total_rows = self._write_validator_file()
        # This runs the rpki validator
        with _run_rpki_validator(self, validator_file, self.rpki_path):
            # First we wait for the validator to load the data
            self._wait_for_validator_load(total_rows)
            # Writes validator to database
            self.logger.debug("validator load completed")
            utils.rows_to_db(self.logger,
                             self._get_ripe_data(),
                             "{}/validity.csv".format(self.csv_dir),  # CSV
                             ROV_Validity_Table)
        utils.delete_paths(self.logger, [validator_file])

########################
### Helper Functions ###
########################

    @error_catcher()
    def _write_validator_file(self):
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
            # This writes the validator file that the rpki validator will use
            # And returns the file path and the total rows of the file
            return table.write_validator_file(path=self.upo_csv_path)

    @error_catcher()
    def _get_ripe_data(self):
        """Gets the data from ripe and formats it for csv insertions"""

        self.logger.info("Getting data from ripe")
        # Then we get the data from the ripe RPKI validator
        # Todo for later, change 10mil to be total count
        url = "http://[::1]:8080/api/bgp/?pageSize=10000000"
        # Gets a list of dictionaries of asns
        asns = utils.get_json(url, self._get_headers())["data"]
        # Changes the validation states to numbers and returns them
        return [self._format_asn_dict(x) for x in asns]

    @staticmethod
    def get_validity_dict():
        """Returns the validity dict for how the info is stored in db.

        This is a static method because it is used in the api.
        """

        return {"VALID": 1,
                "UNKNOWN": 0,
                "INVALID_LENGTH": -1,
                "INVALID_ASN": -2}

    @error_catcher()
    def _format_asn_dict(self, asn):
        """Formats json objects for csv rows"""

        valid = RPKI_Validator.get_validity_dict()
        return [int(asn["asn"][2:]), asn["prefix"], valid.get(asn["validity"])]

    @error_catcher()
    def _get_row_count(self, headers):
        """Returns row count of json object for waiting"""

        try:
            # Gets row count
            return utils.get_json("http://[::1]:8080/api/bgp/",
                                  headers)["metadata"]["totalCount"]
        except Exception as e:
            self.logger.debug("Problem with getting json: {}".format(e))
            return 0

    @error_catcher()
    def _serve_file(self, path):
        """Makes a simple http server and serves a file in /tmp"""

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        # Changes directory to be in /tmp
        os.chdir("/tmp/")
        # Serve the file on port 8000
        socketserver.TCPServer(("", 8000), Handler).serve_forever()

    @error_catcher()
    def _wait_for_validator_load(self, total_rows):
        """Waits for the rpki validator to load all of it's data"""

        time.sleep(30)
        # Check if the rows of the RPKI data are equal to the rows
        # in the unique prefix origins file
        while self._get_row_count(self._get_headers()) < total_rows:
            self.logger.info("Waiting for validator load")
            self.logger.debug(total_rows)
            self.logger.debug(self._get_row_count(self._get_headers()))
            time.sleep(30)

    @error_catcher()
    def _get_headers(self):
        """Returns the proper headers for the requests module"""

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
