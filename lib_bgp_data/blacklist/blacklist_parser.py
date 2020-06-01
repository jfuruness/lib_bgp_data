#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the blacklist parser

The purpose of this class is to download a list of blacklisted ASNs from UCEPROTECT's level 2 and 3 blacklists, Spamhaus's ASN blacklist, and the results from a MIT paper, and insert them into a database. For more information on sources, please see the readme at github.com/nickup9/blacklist_parser
"""
__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner", "UCEPROTECT.net", "Spamhaus.org", "MIT", "CAIDA"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = Development

import requests
import io
import os
import gzip
import re
import csv
from .tables import Blacklist_Table
from ..utils import utils

class Blacklist_Parser:
    
    def _run(self):
        """Downloads and stores ASNs"""
        # Make a new dir for the blacklist
        # Error handling necessary as mkdir will stop if dir exists
        try:
            os.mkdir('blacklist')
        except FileExistsError:
            pass

        os.chdir('blacklist')
        cwd = os.getcwd()
        self._get_blacklists(cwd)
        asn_list = self._parse_lists(cwd)
        with Blacklist_Table(clear=True) as table:
            _csv_dir = f"{self.csv_dir}/blacklist.csv"
            utils.rows_to_db(asn_list, _csv_dir, table)
            table._create_index()

######################
###Helper Functions###
######################

    def _get_blacklists(self, cwd):
        url_name_pair = [('http://wget-mirrors.uceprotect.net/rbldnsd-all/dnsbl-2.uceprotect.net.gz', 'uce_level_two.txt'),
                         ('http://wget-mirrors.uceprotect.net/rbldnsd-all/dnsbl-3.uceprotect.net.gz', 'uce_level_three.txt'),
                         ('https://www.spamhaus.org/drop/asndrop.txt', 'spamhaus_drop.txt'),
                         ('https://raw.githubusercontent.com/ctestart/BGP-SerialHijackers/master/prediction_set_with_class.csv', 'mit_results.csv')]
        for pair in url_name_pair:
            url, filename = pair[0], pair[1]
            downloaded_file = requests.get(url)
            file_path = cwd + '/' + filename
            with open(file_path, 'w') as f:
                f.write(downloaded_file.text)

    def _parse_lists(self, cwd):
        filenames = ['uce_level_two.txt', 'uce_level_three.txt', 'spamhaus_drop.txt', 'mit_results.csv']
        asn_list = []
        for filename in filenames:
            file_path = cwd + '/' + filename
            with open(file_path, 'r') as f:
                asn_list = asn_list + re.findall(r'AS\d+', f.read())

        # Parse the MIT
        with open(mit_filename, newline = '') as f:
            mit_reader = csv.DictReader(f, delimiter = ',')
            for row in mit_reader:
                if row['HardVotePred'] == '1':
                    asn_list.append(row['ASN'])

        # Convert list to dict and back to list again to remove duplicates.
        asn_list = list(dict.fromkeys(asn_list))
        # Remove all 'AS' substring
        for asn in asn_list:
            asn.replace('AS', '')
        return asn_list
