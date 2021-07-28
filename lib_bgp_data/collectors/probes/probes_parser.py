#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains Probes Parser

The purpose of this class is to download probes
from ripe atlas and insert them
into a database. See README for in depth explanation
"""

__authors__ = ["Cameron Morris", "Justin Furuness"]
__credits__ = ["Cameron Morriss", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Cameron Morris"
__email__ = "cameron.morris@uconn.edu"
__status__ = "Development"


import logging
import os

from .tables import Probes_Table

from ...utils.base_classes import Parser
from ...utils import utils


class Probes_Parser(Parser):
    """This class downloads probes from ripe atlas"""

    def _run(self):
        self._install()
        #self._download_probe_file()
        ############################### DELETE LATER@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22
        utils.run_cmds(f"cp /tmp/all_atlas_probes.txt {self.raw_probes_path}")
        self._convert_raw_probes_to_csv()
        utils.csv_to_db(Probes_Table, self.probes_csv_path, clear_table=True)

    def _install(self):
        logging.warning("implement later: sudo apt-get install python-dev libffi-dev libssl-dev")

    def _download_probe_file(self):
        """Gets raw probe information"""

        logging.info("About to download probe file. This takes ~30m")
        utils.run_cmds("ripe-atlas probe-search --field id "
                       "--field asn_v4 --field country --field "
                       "status --field prefix_v4 --field "
                       "is_public --field address_v4 --field "
                       f"is_anchor --status 1 --all > {self.raw_probes_path}")

    def _convert_raw_probes_to_csv(self):
        """Converts raw probe file to CSV"""

        #!/bin/bash

        # 1 and 2: remove the b and the quotes
        # 3 through 6: Map the connection status to true/false
        # 7, 8, and 9: Remove the column headers and last line
        # 10: remove emtpy lines
        # 11: remove disconnected probes
        # 12, 13, and 14: Fill in 'None' for missing values
        # 15, 16: Map the binary values for is_public and is_probe to true/false
        # 17: Replace spaces with commas
        # 18: Remove trailing comma

        utils.run_cmds(r"""
            sed -e "s/^b'//" \
                -e "s/'$//" \
                -e 's/Never Connected/false/' \
                -e 's/Connected/true/' \
                -e 's/Abandoned/false/' \
                -e 's/Disconnected/false/' \
                -e '/=\+/d' \
                -e '/ID.*/d' \
                -e '/Showing/d' \
                -e '/^$/d' \
                -e '/false/d' \
                -e 's/^\([[:digit:]]\+\) \+\([[:alpha:]][[:alpha:]]\)/\1\tNone\t\2/' \
                -e 's/^\([[:digit:]]\+ \+[[:digit:]]\+\) \+\(true\)/\1\tNone\t\2/' \
                -e 's/^\([[:digit:]]\+\tNone\t\)\+\(true\)/\1None\t\2/' \
                -e 's/\\xe2\\x9c\\x98/false/g' \
                -e 's/\\xe2\\x9c\\x94/true/g' \
                -e 's/[[:space:]]\+/\t/g' \
                -e 's/\t$//' \
                -e 's/None//g' """ + self.raw_probes_path + f"> {self.probes_csv_path}")
        logging.info("CSV written")
        return



        with open(self.raw_probe_path, "r") as f:
            lines = f.readlines()

        rows = []
        # Skip first three lines because they are garbage
        for i, line in enumerate(lines[3:]):
            print("MUST fix this. Some rows are empty, so making all spaces just one space will mess this up. Also, some columsn like status can have words separated by spaces like never connected")
            # Make only one space between each
            formatted_line = " ".join(line.split())
            # Remove random b at start, and random quote at start/end
            formatted_line = formatted_line.replace("b'", "").replace("'", "")
            formatted_line.replace("\n", "").replace("\t", "").strip()
            # Get rid of weird last character
            formatted_line = formatted_line[:-1]

            (raw_id,
             raw_asn_v4,
             raw_country,
             raw_connected,
             raw_prefix_v4,
             raw_public,
             raw_address_v4,
             raw_anchor) = formatted_line.split()
            _id = int(raw_id)
            asn_v4 = int(asn_v4)
            connected = True if raw_status == "Connected" else False
            prefix_v4 = raw_prefix_v4 if raw_prefix_v4 != "None" else None
            print(i, line, "!" + formatted_line + "!")
            input()

    @property
    def probes_csv_path(self):
        return os.path.join(self.csv_dir, "probes.csv")

    @property
    def raw_probes_path(self):
        return os.path.join(self.path, "probes.txt")
