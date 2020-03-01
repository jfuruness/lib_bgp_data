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

from multiprocess import Process
import os
import time

from psutil import process_iter
from signal import SIGTERM
import urllib

from .tables import Unique_Prefix_Origins_Table, ROV_Validity_Table
from ..utils import utils

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# Must have this here so that the class can access it when setting attrs
RPKI_PACKAGE_PATH = "/var/lib/rpki-validator-3/"
RPKI_RUN_NAME = "rpki-validator-3.sh"

class RPKI_Validator_Wrapper:
    """This class gets validity data from ripe"""

    __slots__ = ['total_announcements']

    # Sorry for the crazy naming scheme, must be done to avoid
    # having install file names in multiple locations
    rpki_package_path = RPKI_PACKAGE_PATH
    rpki_run_name = RPKI_RUN_NAME
    rpki_run_path = RPKI_PACKAGE_PATH + RPKI_RUN_NAME
    rpki_db_paths = [RPKI_PACKAGE_PATH + x for x in ["db/", "rsync/"]]
    api_url = "http://[::1]:8080/api/"

#################################
### Context Manager Functions ###
#################################

    def __enter__(self):
        """Runs the RPKI Validator"""

        self._kill_8080()
        # Must remove these to ensure a clean run
        utils.clean_paths(self.logger, self.rpki_db_paths)
        cmds = [f"cd {self.rpki_package_path}",
                f"chown -R root:root {self.rpki_package_path}"]
        check_call(" && ".join(cmds), shell=True)
        # Writes validator file and serves it
        with RPKI_File() as rpki_file:
            self._process = Process(target=self._start_validator)
            self.total_announcements = rpki_file.total_lines
            return self

    def __exit__(self, type, value, traceback):
        """Closes RPKI Validator"""

        self._process.terminate()
        self._process.join()
        self.kill_8080(wait=False)
        self.logger.debug("Closed rpki validator")
        return True

    # https://stackoverflow.com/a/20691431
    def _kill_8080(self, wait=True):
        """Kills all processes on port 8080"""

        self.logger.info("Make way for the rpki validator!!!")
        self.logger.debug("Killing all port 8080 processes, cause idc")
        for proc in process_iter():
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == 8080:
                    proc.send_signal(SIGTERM) # or SIGKILL
                    if wait:
                        self._wait(120, "Waiting for ports to be reclaimed")
#        check_call("sudo kill -9 $(lsof -t -i:8080)", shell=True)

    def _start_validator(self):
        """Sends start cmd to RPKI Validator"""

        self.logger.info("Starting RPKI Validator")
        utils.run_cmd(("cd {self.rpki_package_path} && "
                       "./{self.rpki_run_name}"))

#########################
### Wrapper Functions ###
#########################

    def load_trust_anchors(self):
        """Loads all trust anchors"""

        utils.write_to_stdout(self.logger,
                              "{datetime.now()}: Loading RPKI Validator")
        time.sleep(60)
        while self._get_validation_status() is False:
            utils.write_to_stdout(self.logger, ".")
        utils.write_to_stdout(self.logger, "\n")
        self._wait(30, "Waiting for upload to bgp preview")

    def make_query(self, api_endpoint: str, data=True) -> dict:
        """Makes query to api of rpki validator"""

        result = utils.get_json(os.path.join(self.api_url, api_endpoint),
                                RPKI_Validator.get_headers())
        return result["data"] if data else result

    def get_validity_data(self):
        """Gets the data from ripe and formats it for csv insertions"""

        self.logger.info("Getting data from ripe")
        # Then we get the data from the ripe RPKI validator
        # Todo for later, change 10mil to be total count
        return self.make_query("bgp/?pageSize=10000000")

########################
### Helper Functions ###
########################

    def _get_validation_status(self):
        """Returns row count of json object for waiting"""

        try:
            for x in self.make_query("trust-anchors/statuses"):
                if x["completedValidation"] is False:
                    # If anything has not been validated return false
                    return False
            # All are validated. Return true
            return True
        except urllib.error.URLError as e:
            self._wait(60, "Connection was refused")
            return False

    @staticmethod
    def get_validity_dict():
        """Returns the validity dict for the RPKI Validator to decode results

        I could have this as a class attribute but too messy I think.
        """

        return {"VALID": 1,
                "UNKNOWN": 0,
                "INVALID_LENGTH": -1,
                "INVALID_ASN": -2}

    @staticmethod
    def get_headers():
        """Gets the headers for all url queries to the validator"""

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

