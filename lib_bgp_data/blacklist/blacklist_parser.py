#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist parser

The purpose of this class is to download a list of blacklisted ASNs from UCEPROTECT's level 2 and 3 blacklists, Spamhaus's ASN blacklist, and the results from a MIT paper, and insert them into a database. For more information on sources, please see the readme at github.com/nickup9/blacklist_parser
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
from io import StringIO
from .tables import Blacklist_Table
from ..base_classes import Parser
from ..utils import utils

class Blacklist_Parser(Parser):
    
    __slots__ = []

    def _run(self):
        """Downloads and stores ASNs to table blacklist with columns uce2, uce3, spamhaus, and mit. Due to constraints when executing SQL, columns will be the size of the column with the most data, with None acting as filler forthe smaller columns where that source has no more ASNs on blacklist"""
        with Blacklist_Table(clear=True) as _blacklist_table:
            raw = (self._parse_lists(self._get_blacklists()))
            asns = self._format_dict(raw)
            _csv_dir = f"{self.csv_dir}/blacklist.csv"
            utils.rows_to_db(asns, _csv_dir, Blacklist_Table)

######################
###Helper Functions###
######################

    def _get_blacklists(self):
        """Gets blacklists from UCE level 2, UCE level 3, spamhaus, and the
        MIT paper, makes a dict for each source, and attaches the 
        blacklist of each source into the respective key as a string
        """
        sources = {'uce2':'http://wget-mirrors.uceprotect.net/rbldnsd-all/dnsbl-2.uceprotect.net.gz', 'uce3':'http://wget-mirrors.uceprotect.net/rbldnsd-all/dnsbl-3.uceprotect.net.gz', 'spamhaus':'https://www.spamhaus.org/drop/asndrop.txt', 'mit':'https://raw.githubusercontent.com/ctestart/BGP-SerialHijackers/master/prediction_set_with_class.csv'}
        output_str = dict()
        for typ in sources.keys():
            output_str[typ] = ''
        # For each source in the sources dict, GET url and save string
        # to dict.
        for source in sources.keys():
            downloaded_file = requests.get(sources[source])
            # UCEPROTECT is inconsistent in that sometimes a python
            # requested file will sometimes come as a txt, sometimes
            # as a tarball that needs to be unzipped. We check this:
            if downloaded_file.headers['Content-Type'] == 'application/octet-stream':
                decompressed = gzip.decompress(downloaded_file.content)
                # UCEPROTECT uses ISO-8859-1 for text, not utf-8
                output_str[source] = decompressed.decode('ISO-8859-1')
            else:
                # We have a txt and save to dict directly
                output_str[source] = downloaded_file.text
        return output_str

    def _parse_lists(self, outputs: dict):
        """For each source in outputs, takes the string attached to
        the source and parses it for ASNs, then saves to dict with
        sources as keys with a list of ASNs
        """
        parsed = dict()
        # For each source in outputs, parse for ASNs and save ASNs as
        # list for each source in dict.
        for output in outputs.keys():
            # If not a mit csv, just regex to find ASNs.
            if output != 'mit':
                parsed[output] = re.findall(r'AS\d+', outputs[output])
            # If mit csv, use csv utilities to ID malicious ASNs.
            if output == 'mit':
                parsed[output] = []
                fake_file = StringIO(outputs[output])
                mit_reader = csv.DictReader(fake_file, delimiter = ',')
                for row in mit_reader:
                    if row['HardVotePred'] == '1':
                        parsed[output].append(row['ASN'])
        # For each key in parsed dictionary, remove duplicates and
        # remove 'AS' from infront of ASN.
        for key in parsed.keys():
            parsed[key] = list(dict.fromkeys(parsed[key]))
            # Remove AS from the the numbers
            for i in range(len(parsed[key])):
                parsed[key][i] = parsed[key][i].replace('AS', '')
        return parsed

    def _format_dict(self, parsed: dict):
        """Takes a dict, with the header as the keys, and converts into a formatted list for input into database"""
        # Constructor for list
        unformatted = []
        formatted = []
        largest = 0
        # For each key in parsed dict, add items of key to list as list
        for source in parsed:
            unformatted.append(parsed[source])
        # For each list in unformatted list, do the following:
        # See if this is the largest list we've worked with
        # Convert items from str to int
        for lst in range(len(unformatted)):
            largest = max(largest, len(unformatted[lst]))
            for i in range(len(unformatted[lst])):
                unformatted[lst][i] = int(unformatted[lst][i])
        # Now to format the list for use with rows_to_db, we gotta turn
        # it 90 degrees, if you could visualize that. We make a list
        # of lists, where each sublist is a row for our DB, and the
        # sublist has the ASNs in the order [uce2, uce3, spamhaus, mit]
        # If a source has no more data, we put None
        for i in range(largest):
            buff = []
            for lst in range(len(unformatted)):
                if len(unformatted[lst]) > i:
                    buff.append(unformatted[lst][i])
                else:
                    buff.append(None)
            formatted.append(buff)
        return formatted
