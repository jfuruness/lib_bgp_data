#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module downloads all the roas from ftp.ripe.net/rpki to the database.
HTML parsing and multiprocessing is the fastest way to do this.
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
        """Collect the paths to all the csvs to download. Multithread the
           downloading of all the csvs, insert into db if not seen before."""

        # maybe not functional?
        parsed = self._get_parsed_files()

        if date is None:
            paths = self._get_csvs(s)
        else:
            paths = self._get_csvs_date(date)

        paths = [p for p in paths if p not in parsed]

        download_paths = self._create_local_download_paths(paths)

        # Multiprocessingly download all csvs (nodes = 4 x # CPUS)
        pool = ProcessPool(nodes=48)
        pool.map(utils.download_file, paths, download_paths)
        pool.map(self._reformat_csv, download_paths)
        pool.map(self._db_insert, download_paths)
        pool.close()
        pool.join()

        with Historical_ROAs_Table() as t:
            t.delete_duplicates()

        self._add_parsed_files(paths)

        utils.delete_paths(self.path)

    def _get_parsed_files(self):
        """Return the csvs that have already been parsed and inserted into db"""

        parsed = []
        with Historical_ROAs_Parsed_Table() as t:
            for row in t.execute(f'SELECT * FROM {t.name}'):
                parsed.append(row['file'])
        return parsed

    def _add_parsed_files(self, files):
        """Adds newly parsed csvs to the parsed table"""
        path = './roas_parsed.csv'
        with open(path, 'w+') as f:
            for line in files:
                f.write(line + '\n')
        utils.csv_to_db(Historical_ROAs_Parsed_Table, path)

    def _create_local_download_paths(self, paths):
        """Create the directories for downloading csvs.
        Return paths."""

        # mkdir all the dirs starting with parent dir 'rpki'
        download_paths = []
        for path in paths:
            download_path = self.path + path[path.index('rpki'):]
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

    def _get_csvs(self, s, root=None, paths=None):
        """
        Returns the paths to all the csvs that exist under root.
        Pass a requests session s for speed.
        """

        if root is None:
            root = self.root
        if paths is None:
            paths = []

        r = self.session.get(root)
        r.raise_for_status()
        # lxml is faster than html.parser
        html = Soup(r.text, 'lxml')
        r.close()

        # the first link is the parent directory
        for link in html('a')[1:]:

            href = link['href']
            path = os.path.join(root, href)

            if href == '/' or href == 'repo.tar.gz':
                pass
            elif 'csv' in href:
                paths.append(path)
            else:
                self._get_csvs(s, path, paths, date)

        return paths

    def _get_csvs_date(self, date):
        """Get all the paths to roas.csv for a specific date."""

        # from the root page, get the links to each internet registry
        paths = []
        for link in self._soup(self.root)('a')[1:]:
            href = link['href']
            registries.append(os.path.join(self.root, href))

        # look in each registry for a csv under date        
        for url_part in date.strftime('%Y/ %m/ %d/').split() + ['roas.csv']:
            # basically tacking on another part of the url each time
            paths = self._get_extensions(paths, url_part)
        
        return paths

    def _get_extensions(self, originals, extension):
        """Returns a new list of urls to that are generated by finding the
        extensions in each original url's page."""

        next_urls = []

        for i in originals:
            next_urls.extend(self._find_href(i, extension))
            
        return next_urls      

    def _find_href(self, link, _href):
        """A helper that looks for a specified href on a page""")

        new_link = self._soup(link).find(href=_href)
        if new_link:
            return [link + new_link['href']]
        else:
            return []

    def _soup(self, url):
        """Returns BeautifulSoup object of url
        using lxml parser (faster than html.parser)."""
        r = self.session.get(link)
        r.raise_for_status()
        html = Soup(r.text, 'lxml')
        r.close()
        return html
