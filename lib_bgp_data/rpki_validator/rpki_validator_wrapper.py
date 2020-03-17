#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class RPKI_Validator

The purpose of this class is to obtain the validity data for all of the
prefix origin pairs in our announcements data, and insert it into a
database. This is done through a series of detailed on README.
"""

from datetime import datetime
import logging
import os
import time

from pathos.multiprocessing import ProcessingPool
from psutil import process_iter
from signal import SIGTERM
from tqdm import trange
import urllib

from .rpki_file import RPKI_File
from .tables import Unique_Prefix_Origins_Table, ROV_Validity_Table
from ..utils import utils, config_logging

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# Must have this here so that the class can access it when setting attrs
RPKI_PACKAGE_PATH = "/var/lib/rpki-validator-3/"
RPKI_RUN_NAME = "rpki-validator-3.sh"

class RPKI_Validator_Wrapper:
    """This class gets validity data from ripe"""

    __slots__ = ['total_prefix_origin_pairs', "_process", "_table_input",
                 "_rpki_file"]

    # Sorry for the crazy naming scheme, must be done to avoid
    # having install file names in multiple locations
    rpki_package_path = RPKI_PACKAGE_PATH
    rpki_run_name = RPKI_RUN_NAME
    rpki_run_path = RPKI_PACKAGE_PATH + RPKI_RUN_NAME
    rpki_db_paths = [RPKI_PACKAGE_PATH + x for x in ["db/", "rsync/"]]
    port = 8080
    api_url = "http://[::1]:8080/api/"

    def __init__(self, **kwargs):
        config_logging(kwargs.get("stream_level", logging.INFO),
                       kwargs.get("section"))
        self._table_input = kwargs.get("table_input", "mrt_rpki")
        if not os.path.exists(self.rpki_package_path):
            logging.warning("Looks like validator is not installed")
            logging.warning("Installing validator now")
            RPKI_Validator_Wrapper.install(**kwargs)

#################################
### Context Manager Functions ###
#################################

    def __enter__(self):
        """Runs the RPKI Validator"""

        self._kill_8080()
        # Must remove these to ensure a clean run
        utils.clean_paths(self.rpki_db_paths)
        cmds = [f"cd {self.rpki_package_path}",
                f"chown -R root:root {self.rpki_package_path}"]
        utils.run_cmds(cmds)
        # Writes validator file and serves it
        # Can't use cntext manager here since it returns it
        self._rpki_file = RPKI_File(self._table_input)
        self._rpki_file.spawn_process()
        self._process = ProcessingPool()
        self._process.apipe(self._start_validator)
        self.total_prefix_origin_pairs = self._rpki_file.total_lines
        return self

    def __exit__(self, type, value, traceback):
        """Closes RPKI Validator"""

        self._process.close()
        self._process.terminate()
        self._process.join()
        self._process.clear()
        self._kill_8080(wait=False)
        logging.debug("Closed rpki validator")
        self._rpki_file.close()

    # https://stackoverflow.com/a/20691431
    def _kill_8080(self, wait=True):
        """Kills all processes on port 8080"""

        logging.debug("Make way for the rpki validator!!!")
        logging.debug("Killing all port 8080 processes, cause idc")
        for proc in process_iter():
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == RPKI_Validator_Wrapper.port:
                    proc.send_signal(SIGTERM) # or SIGKILL
                    # Sometimes the above doesn't do it's job
                    utils.run_cmds(("sudo kill -9 $(lsof -t -i:"
                                    f"{RPKI_Validator_Wrapper.port})"))
                    if wait:
                        self._wait(120, "Waiting for reclaimed ports")

    def _start_validator(self):
        """Sends start cmd to RPKI Validator"""

        logging.info("Starting RPKI Validator")
        utils.run_cmds((f"cd {self.rpki_package_path} && "
                        f"./{self.rpki_run_name}"))

#########################
### Wrapper Functions ###
#########################

    def load_trust_anchors(self):
        """Loads all trust anchors"""

        utils.write_to_stdout(f"{datetime.now()}: Loading RPKI Validator\n",
                              logging.root.level)
        time.sleep(60)
        while self._get_validation_status() is False:
            time.sleep(10)
            utils.write_to_stdout(".", logging.root.level)
        utils.write_to_stdout("\n", logging.root.level)
        self._wait(30, "Waiting for upload to bgp preview")

    def make_query(self, api_endpoint: str, data=True) -> dict:
        """Makes query to api of rpki validator"""

        result = utils.get_json(os.path.join(self.api_url, api_endpoint),
                                RPKI_Validator_Wrapper.get_headers())
        return result["data"] if data else result

    def get_validity_data(self) -> dict:
        """Gets the data from ripe and formats it for csv insertions"""

        logging.info("Getting data from ripe")
        assert self.total_prefix_origin_pairs < 10000000, "page size too small"
        # Then we get the data from the ripe RPKI validator
        # Todo for later, change 10mil to be total count
        return self.make_query("bgp/?pageSize=10000000")

########################
### Helper Functions ###
########################

    def _wait(self, time_to_sleep: int, msg: str):
        """logs a message and waits"""

        logging.debug(msg)
        if logging.root.level == logging.INFO:
            # Number of times per second to update tqdm
            divisor = 100
            for _ in trange(time_to_sleep * divisor,
                            desc=msg):
                time.sleep(1 / divisor)

    def _get_validation_status(self) -> bool:
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

######################
### Static methods ###
######################

    @staticmethod
    def get_validity_dict() -> dict:
        """Returns the validity dict for the RPKI Validator to decode results

        I could have this as a class attribute but too messy I think.
        """

        return {"VALID": 1,
                "UNKNOWN": 0,
                "INVALID_LENGTH": -1,
                "INVALID_ASN": -2}

    @staticmethod
    def get_headers() -> dict:
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

#########################
### Install Functions ###
#########################

    @staticmethod
    def install(**kwargs):
        """Installs RPKI validator with our configs.

        This might break in the future, but we need to do it this way
        for now to be able to do what we want with our own prefix origin
        table.
        """

        config_logging(kwargs.get("stream_level", logging.DEBUG),
                       kwargs.get("section"))
        utils.delete_paths(RPKI_Validator_Wrapper.rpki_package_path)

        RPKI_Validator_Wrapper._download_validator()
        RPKI_Validator_Wrapper._change_file_hosted_location()
        path = RPKI_Validator_Wrapper._change_server_address()
        RPKI_Validator_Wrapper._config_absolute_paths(path)

    @staticmethod
    def _download_validator():
        """Downloads validator into proper location"""

        rpki_url = ("https://ftp.ripe.net/tools/rpki/validator3/beta/generic/"
                    "rpki-validator-3-latest-dist.tar.gz")
        arin_tal = ("https://www.arin.net/resources/manage/rpki/"
                    "arin-ripevalidator.tal")
        # This is the java version they use so we will use it
        cmds = ["sudo apt-get -y install openjdk-8-jre",
                f"wget {rpki_url}",
                "tar -xvf rpki-validator-3-latest-dist.tar.gz",
                "rm -rf rpki-validator-3-latest-dist.tar.gz",
                f"mv rpki-validator* {RPKI_Validator_Wrapper.rpki_package_path}",
                f"cd {RPKI_Validator_Wrapper.rpki_package_path}",
                "cd preconfigured-tals",
                f"wget {arin_tal}"]
        utils.run_cmds(cmds)

    @staticmethod
    def _change_file_hosted_location():
        """Changes location of input ann for bgp preview file"""

        # Changes where the file is hosted
        path = (f"{RPKI_Validator_Wrapper.rpki_package_path}conf"
                "/application-defaults.properties")
        prepend = "rpki.validator.bgp.ris.dump.urls="
        replace = ("https://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz,"
                   "https://www.ris.ripe.net/dumps/riswhoisdump.IPv6.gz")
        replace_with = (f"http://localhost:{RPKI_File.port}"
                        f"/{RPKI_File.hosted_name}")
        utils.replace_line(path, prepend, replace, replace_with)

    @staticmethod
    def _change_server_address():
        """Prob because of a proxy, but on our server this is necessary"""

        # Changes the server address
        path = (f"{RPKI_Validator_Wrapper.rpki_package_path}conf"
                "/application.properties")
        prepend = "server.address="
        replace = "localhost"
        replace_with = "0.0.0.0"
        utils.replace_line(path, prepend, replace, replace_with)
        return path

    @staticmethod
    def _config_absolute_paths(path):
        """Configure rpki validator to run off absolute paths

        This is necessary due to script being called from elsewhere
        In other words not from inside the RPKI dir.
        """

        # Since I am calling the script from elsewhere these must be
        # absolute paths
        prepend = "rpki.validator.data.path="
        replace = "."
        # Must remove trailing backslash at the end
        replace_with = RPKI_Validator_Wrapper.rpki_package_path[:-1]
        utils.replace_line(path, prepend, replace, replace_with)

        prepend = "rpki.validator.preconfigured.trust.anchors.directory="
        replace = "./preconfigured-tals"
        replace_with = (f"{RPKI_Validator_Wrapper.rpki_package_path}"
                        "preconfigured-tals")
        utils.replace_line(path, prepend, replace, replace_with)

        prepend = "rpki.validator.rsync.local.storage.directory="
        replace = "./rsync"
        replace_with = f"{RPKI_Validator_Wrapper.rpki_package_path}rsync"
        utils.replace_line(path, prepend, replace, replace_with)
