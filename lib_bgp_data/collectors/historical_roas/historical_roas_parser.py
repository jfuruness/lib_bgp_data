#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module downloads all the ROAs from ftp.ripe.net/rpki or all the ROAs
that exist for a specific date.

Processing the HTML from the server has been tested to be faster than
using Python's built-in FTP library.

Guidelines:
1. Maintain a table of files that have been parsed.
2. Extract the URLs. This step is not multiprocessed.
3. Use the URLs to multiprocess the downloading, reformatting, and insertion
of all roas.csv files.
"""

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
from pathos.multiprocessing import ProcessPool
import requests
from bs4 import BeautifulSoup as Soup
from datetime import datetime

from ...utils.base_classes import Parser
from ...utils import utils
from .tables import Historical_ROAs_Table, Historical_ROAs_Parsed_Table


class Historical_ROAs_Parser(Parser):

    session = requests.Session()
    root = 'https://ftp.ripe.net/rpki'

    def _run(self, date: datetime = None):
        """Pass a datetime object to get ROAs for specified date
         or default to getting all ROAs."""

        if date is None:
            urls = self._get_csvs()
        else:
            urls = self._get_csvs_date(date)

        parsed = self._get_parsed_files()

        urls = [url for url in urls if url not in parsed]

        download_paths = self._create_local_download_paths(urls)

        # Multiprocessingly download/format/insert all csvs
        # using four times # of CPUs
        with utils.Pool(0, 4, self.name) as pool:
            pool.map(utils.download_file, urls, download_paths)
            pool.map(self._reformat_csv, download_paths)
            pool.map(self._db_insert, download_paths)

        with Historical_ROAs_Table() as t:
            t.delete_duplicates()

        self._add_parsed_files(urls)

        utils.delete_files(self.path)

    def _get_parsed_files(self):
        """Return the csvs that have already been parsed and inserted into db"""

        parsed = []
        with Historical_ROAs_Parsed_Table() as t:
            for row in t.execute(f'SELECT * FROM {t.name}'):
                parsed.append(row['file'])
        return parsed

    def _add_parsed_files(self, files):
        """Adds newly parsed csvs to the parsed table"""
        path = os.path.join(self.path, 'roas_parsed.csv')
        with open(path, 'w+') as f:
            for line in files:
                f.write(line + '\n')
        utils.csv_to_db(Historical_ROAs_Parsed_Table, path)

    def _create_local_download_paths(self, urls):
        """Create the local directories where csvs will be downloaded to."""

        # URL: https://ftp.ripe.net/rpki/afrinic.tal/2019/08/01/roas.csv
        # Path: /tmp/bgp_Historical_ROAs_Parser/rpki/2019/08/01/

        download_paths = []
        for url in urls:
            download_path = os.path.join(self.path, url[url.index('rpki'):])
            # p flag creates necessary parent directories
            # slicing off the 'roas.csv'
            utils.run_cmds(f'mkdir -p {download_path[:-8]}')
            download_paths.append(download_path)

        return download_paths

    def _reformat_csv(self, csv):
        """Delete URI (1st) column using cut,
           delete the first row (column names),
           delete 'AS', add the date, replace commas with tabs using sed"""

        date = '-'.join(csv[-19:-9].split('/'))
        cmds = [f'cut -d , -f 1 --complement <{csv} >{csv}.new',
                f'mv {csv}.new {csv}',
                f'sed -i "1d" {csv}',
                f'sed -i "s/AS//g" {csv}',
                f'sed -i "s/,/\t/g" {csv}',
                f'sed -i "s/$/\t{date}/" {csv}']

        utils.run_cmds(cmds)

    def _db_insert(self, csv):
        utils.csv_to_db(Historical_ROAs_Table, csv)

    def _get_csvs(self):#, root=None, paths=None):
        """
        Returns the paths to all the csvs that exist under root.
        """

        #if root is None:
        #    root = self.root
        #if paths is None:
        #    paths = []

        # Iterative depth-first search
        stack = [self.root]
        urls = []

        while stack:
            curr_dir = stack.pop()

            # skip first link which is always the parent dir    
            for link in self._soup(curr_dir)('a')[1:]:
                href = link['href']
                next_link = os.path.join(curr_dir, href)

                # Case 1: found the csv, add it to the list of URLs we return
                # Case 2: Empty dir or repo.tar.giz. Ignore.
                # Case 3: DFS further down
                if 'csv' in href:
                    urls.append(next_link)
                elif href != '/' and href != 'repo.tar.gz':
                    stack.append(next_link)

        # skip first link (parent directory)
        #for link in self._soup(root)('a')[1:]:

        #    href = link['href']
        #    path = os.path.join(root, href)

        #    if href == '/' or href == 'repo.tar.gz':
                pass
        #    elif 'csv' in href:
        #        paths.append(path)
        #    else:
        #        self._get_csvs(s, path, paths, date)

        return urls

    def _get_csvs_date(self, date):
        """Get all the paths to roas.csv for a specific date."""

        # from the root page, get the links to each internet registry
        paths = []
        for registry in self._soup(self.root)('a')[1:]:
            paths.append(os.path.join(self.root, registry['href']))

        # complete the url by adding the date and 'roas.csv'
        date_as_url = date.strftime('%Y/%m/%d/') 
        for i in range(len(paths)):
            paths[i] = os.path.join(paths[i], date_as_url, 'roas.csv')
        
        # return the paths that exists
        return [p for p in paths if self.session.get(p).status_code == 200]
            
    def _soup(self, url):
        """Returns BeautifulSoup object of url."""
        r = self.session.get(url)
        r.raise_for_status()
        html = Soup(r.text, 'lxml') # lxml is fastert than html.parser
        r.close()
        return html
