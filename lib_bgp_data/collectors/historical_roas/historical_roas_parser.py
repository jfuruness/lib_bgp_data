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

    def _run(self, date=None): # ,  year=None, month=None, day=None):
        """Collect the paths to all the csvs to download. Multithread the
           downloading of all the csvs, insert into db if not seen before."""

        # maybe not functional?
        parsed = self._get_parsed_files()

        s = requests.Session()

        if date is None:
            paths = self._get_csvs(s)
        else:
            y, m, d = self.validate_date(date)
            paths = self._get_csvs_date(s, year=y, month=m, day=d)

        paths = [p for p in paths if p not in parsed]

        # generate the list of all download_paths
        # mkdir all the dirs starting with parent dir 'rpki'
        download_paths = []
        for path in paths:
            download_path = path[path.index('rpki'):]
            utils.run_cmds(f'mkdir -p {download_path[:-8]}')
            download_paths.append(download_path)

        # Multiprocessingly download all csvs (nodes = 4 x # CPUS)
        pool = ProcessPool(nodes=48)
        pool.map(utils.download_file, paths, download_paths)
        pool.map(self._reformat_csv, download_paths)
        pool.map(self._db_insert, download_paths)
        pool.close()
        pool.join()

        with Historical_ROAS_Table() as t:
            t.delete_duplicates()

        self._add_parsed_files(paths)

        utils.delete_paths('./rpki')

    def validate_date(self, date):
        """Validates date and extracts year, month, and day (zero-padded)"""
        d = datetime.strptime(date, '%Y-%m-%d').isoformat()
        return d[:4], d[5:7], d[8:10]

    def _get_parsed_files(self):
        """Return the csvs that have already been parsed and inserted into db"""

        parsed = []
        with Historical_ROAS_Parsed_Table() as t:
            for row in t.execute(f'SELECT * FROM {t.name}'):
                parsed.append(row['file'])
        return parsed

    def _add_parsed_files(self, files):
        """Adds newly parsed csvs to the parsed table"""
        path = './roas_parsed.csv'
        with open(path, 'w+') as f:
            for line in files:
                f.write(line + '\n')
        utils.csv_to_db(Historical_ROAS_Parsed_Table, path)

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
        utils.csv_to_db(Historical_ROAS_Table, csv)

    def _get_csvs(self, s, root='https://ftp.ripe.net/rpki', paths=None):
        """
        Returns the paths to all the csvs that exist under root.
        Pass a requests session s for speed.
        """

        if paths is None:
            paths = []

        r = s.get(root)
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

    def _get_csvs_date(self, s, root='https://ftp.ripe.net/rpki',
                       year=None, month=None, day=None):
        """Get all the paths to roas.csv for a specific date."""

        r = s.get(root)
        r.raise_for_status()
        html = Soup(r.text, 'lxml')
        r.close()

        # first, get the links to each internet registry
        registries = []
        for link in html('a')[1:]:
            href = link['href']
            registries.append(os.path.join(root, href))

        # then narrowing it down the the year
        years = []
        for i in registries:
            years.append(self._find_hrefs(s, i, year+'/'))

        # narrow it down further to specific month
        months = []
        for y in years:
            months.append(self._find_hrefs(s, y, month+'/'))

        days = []
        for m in months:
            days.append(self._find_hrefs(s, m, day+'/'))

        # finally can get the csvs
        csvs = []
        for d in days:
            csvs.append(self._find_href(s, d, 'roas.csv'))

        return csvs

    def _find_href(self, req_ses, link, _href):
        """A helper that looks for a specified href on a page"""
        r = req_ses.get(link)
        r.raise_for_status()
        html = Soup(r.text, 'lxml')
        r.close()

        return html(href=_href)['href']
        
