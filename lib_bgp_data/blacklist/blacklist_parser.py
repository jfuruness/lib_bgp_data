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
import os
import gzip
import re
import csv
import sys
from io import StringIO
from .tables import Blacklist_Table
from ..base_classes import Parser
from ..utils import utils

class Blacklist_Parser(Parser):
    
    def _run(self):
        """Downloads and stores ASNs"""
        with Blacklist_Table(clear=True) as table:
            # Stuff goes here
            raw = (self._parse_lists(self, self._get_blacklists(self)))
            asns = self._format_dict(self, raw)
            _csv_dir = f"{self.csv_dir}/roas.csv"
            utils.rows_to_db(asns, _csv_dir, Blacklist_Table)
            table._create_index()

######################
###Helper Functions###
######################

    def _get_blacklists(self):
        """Gets blacklists from UCE level 2, UCE level 3, spamhaus, and the
        MIT paper, makes a dict for each source, and puts the blacklist of          each source into the respective key's list.
        """
        sources = {'uce2':'http://wget-mirrors.uceprotect.net/rbldnsd-all/dnsbl-2.uceprotect.net.gz', 'uce3':'http://wget-mirrors.uceprotect.net/rbldnsd-all/dnsbl-3.uceprotect.net.gz', 'spamhaus':'https://www.spamhaus.org/drop/asndrop.txt', 'mit':'https://raw.githubusercontent.com/ctestart/BGP-SerialHijackers/master/prediction_set_with_class.csv'}
        output_str = dict()
        for typ in sources.keys():
            output_str[typ] = ''
        for source in sources.keys():
            downloaded_file = requests.get(sources[source])
            if downloaded_file.headers['Content-Type'] == 'application/octet-stream':
                decompressed = gzip.decompress(downloaded_file.content)
                output_str[source] = decompressed.decode('utf-8')
            else:
                output_str[source] = downloaded_file.text
        return output_str

    def _parse_lists(self, outputs: dict):
        parsed = dict()
        for output in outputs.keys():
            if output != 'mit':
                parsed[output] = re.findall(r'AS\d+', outputs[output])
            if output == 'mit':
                parsed[output] = []
                fake_file = StringIO(outputs[output])
                mit_reader = csv.DictReader(fake_file, delimiter = ',')
                for row in mit_reader:
                    if row['HardVotePred'] == '1':
                        parsed[output].append(row['ASN'])
        for key in parsed.keys():
            parsed[key] = list(dict.fromkeys(parsed[key]))
            # Remove AS from the the numbers
            for i in range(len(parsed[key])):
                result = parsed[key][i].replace('AS', '')
                if result == None:
                    print('Result is none')
                if result == '':
                    print('Result is blanks')
                parsed[key][i] = parsed[key][i].replace('AS', '')
        for key in parsed.keys():
            if parsed[key] == []:
                print(key + ' is empty')
        return parsed

    def _format_dict(self, parsed: dict):
        """Takes a dict, with the header as the keys, and converts into a csv formatted string for input into database"""
        fake_file = StringIO()
        writer = csv.writer(fake_file)
        for key, value in parsed.items():
            writer.writerow([key, value])
        return fake_file.getvalue()
