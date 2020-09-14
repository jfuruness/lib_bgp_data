#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist parser

The purpose of this class is to download a list of blacklisted ASNs
from UCEPROTECT's level 2 and 3 blacklists, Spamhaus's ASN blacklist,
and the results from a MIT paper, and insert them into a database.
For more information on sources, please see the readme at
github.com/nickup9/blacklist_parser
"""
__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import requests
import io
import gzip
import re
import csv
import time
import os
from io import StringIO
from .tables import Blacklist_Table
from ..base_classes import Parser
from ..utils import utils


class Blacklist_Parser(Parser):

    __slots__ = []

    def _run(self):
        """Downloads and stores ASNs to table blacklist with columns
        uce2, uce3, spamhaus, and mit. Due to constraints when
        executing SQL, columns will be the size of the column with
        the most data, with None acting as filler for the smaller
        columns where that source has no more ASNs on blacklist"""
        with Blacklist_Table(clear=True) as _blacklist_table:
            # Get and format asns
            raw = self._parse_lists(self._get_blacklists())
            asns = self._format_dict(raw)
            _csv_dir = f"{self.csv_dir}/blacklist.csv"
            utils.rows_to_db(asns, _csv_dir, Blacklist_Table)

######################
###Helper Functions###
######################
    def _check_file(self, f):
        """Takes a requests file and returns true if it has content,
        false otherwise.
        """
        return (f.ok and f.content) != ''

    def _get_blacklists(self):
        """Gets blacklists from UCE level 2, UCE level 3, spamhaus, and the
        MIT paper, makes a dict for each source, and attaches the
        blacklist of each source into the respective key as a path to file
        """

        # Download sources to file, and then read from file instead of
        # reading from string, makes more sense/readable DONE
        # Why am I using an IP for UCE's mirrors? The various mirrors
        # of UCE's blacklists are not consistent with one another:
        # Some will return a gzip, some just ISO-8859 text, and some
        # just don't work. So, to ensure consistency, I'm using IP.
        # This should return plaintext.
        sources = {'uce2': 'http://72.13.86.154/rbldnsd-all/dnsbl-2.uceprotect.net.gz',
                   'uce3': 'http://72.13.86.154/rbldnsd-all/dnsbl-3.uceprotect.net.gz',
                   'spamhaus': 'https://www.spamhaus.org/drop/asndrop.txt',
                   'mit': 'https://raw.githubusercontent.com/ctestart/BGP-SerialHijackers/master/prediction_set_with_class.csv'}
        output_path = dict()
        # For each source in the sources dict, GET url, write response
        # to path, and save path to dict.
        for source in sources:
            downloaded_file = requests.get(sources[source])
            # Now we'll check if we got a proper file, if not try 5
            # more times or until success
            if not self._check_file(downloaded_file):
                for i in range(5):
                    # Don't want to spam the page
                    time.sleep(5)
                    downloaded_file = requests.get(sources[source])
                    if self._check_file(downloaded_file):
                        break
            if not self._check_file(downloaded_file):
                raise requests.exceptions.RetryError(
                      "Aborting: File from " + source +
                      " failed to download properly with status code" +
                      str(downloaded_file.status_code) + "and length" +
                      str(len(downloaded_file.content)))
                raise SystemExit("Aborting")
            _path = f"{self.path}/" + source
            with open(_path, 'w+') as f:
                f.write(downloaded_file.text)
                output_path[source] = _path
        return output_path

    def _parse_lists(self, sources: dict):
        """For each source in outputs, takes the string attached to
        the source and parses it for ASNs, then saves to dict with
        sources as keys with a list of ASNs
        """
        parsed = dict()
        # For each source in outputs, parse for ASNs and save ASNs as
        # list for each source in dict.
        for source in sources:
            # If not a mit csv, just regex to find ASNs.
            if source != 'mit':
                with open(sources[source], 'r') as f:
                    output = f.read()
                    asns = re.findall(r'AS(\d+)', output)
                    parsed[source] = set(asns)
            # If mit csv, use csv utilities to ID malicious ASNs.
            elif source == 'mit':
                parsed[source] = set()
                with open(sources[source], newline='') as csvfile:
                    mit_reader = csv.DictReader(csvfile, delimiter=',')
                    for row in mit_reader:
                        # Column 54 is HardVotePred: If 1, MIT's
                        # classifier has flagged the ASN
                        # as having a similar behavior to BGP serial
                        # hijackers. If 0, the ASN was not flagged.
                        if row['HardVotePred'] == '1':
                            parsed[source].update(set(row['ASN']))
        return parsed

    def _format_dict(self, parsed: dict):
        """Takes a dict, with the source as the keys, and converts into
        a formatted list for input into database"""
        formatted = []
        for key in parsed:
            for asn in parsed[key]:
                formatted.append([asn, key])
        return formatted
