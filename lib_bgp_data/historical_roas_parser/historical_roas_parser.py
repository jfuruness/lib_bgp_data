#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser takes 10+ hours.
Downloads 10,000+ csvs
"""

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
from ftplib import FTP, error_perm
import threading
from queue import Queue
import time
from pathos.multiprocessing import ProcessPool
import subprocess
import requests
from bs4 import BeautifulSoup as Soup

from ..base_classes import Parser
from ..utils import utils
from .tables import Historical_ROAS_Table, Historical_ROAS_Parsed_Table


class Historical_ROAS_Parser(Parser):

    count = 0

    def _run(self):
        """Collect the paths to all the csvs to download. Multithread the
           downloading of all the csvs, insert into db if not seen before."""

        # this machine has 12 cpus
        # ProcessPool(nodes=48).map(self.download_csvs_test, [])
        
        #csv_paths = self.get_csvs()

        # self.get_csvs_parse()

        # FTP for paths takes ~ 4 hrs
        #with FTP('ftp.ripe.net') as ftp:
         #   ftp.login()
          #  print(self.get_csvs(ftp, 'rpki'))

        
        s = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '\
                         'AppleWebKit/537.36 (KHTML, like Gecko) '\
                       'Chrome/75.0.3770.80 Safari/537.36'}
        s.headers.update(headers)

        paths = self.get_csvs_parse(s)

        print(f'Done parsing {len(paths)} csvs')

        # generate the list of all download_paths
        # mkdir all the dirs starting with parent dir 'rpki'
        download_paths = []
        for path in paths:
            download_path = path[path.index('rpki'):]
            utils.run_cmds(f'mkdir -p {download_path[:-8]}')
            download_paths.append(download_path)
        
        print(f'There are {len(download_paths)} download_paths')

        # Multiprocessingly download all csvs (nodes = 4 x # CPUS)
        pool = ProcessPool(nodes=48)
        pool.map(utils.download_file, paths, download_paths)
        pool.map(self.reformat_csv, download_paths)
        pool.map(self.db_insert, download_paths)
        pool.close()
        pool.join()


    def download_csvs_test(self):

        # wget all the csv files - 2 hrs
        p = subprocess.run('wget -r -np -e robots=off -A "*.csv" ftp.ripe.net/rpki/',
            shell=True)

        # list the paths to each csv
        output = subprocess.run(f'find {os.getcwd()} -type f',
                            shell=True, capture_output=True)

        for csv in output.split('\n'):
            self.reformat_csv(csv)
            utils.csv_to_db(Historical_ROAS_Table, csv)

    def reformat_csv(self, csv):
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

    def db_insert(self, csv):
        utils.csv_to_db(Historical_ROAS_Table, csv)
        with Historical_ROAS_Table() as t:
            t.delete_duplicates()

    def wget_try(self):
        check_call('wget -r -np -R "repo.tar.gz" ftp.ripe.net/rpki/', shell=True)

    def get_csvs(self, ftp, root, paths=None):
        """Return list of URLs to all CSVs on the FTP server."""

        if paths is None:
            paths = []

        for path in ftp.nlst(root):
            if 'csv' in path:
                paths.append(path)
            elif 'repo.tar.gz' in path:
                pass
            else:
                self.get_csvs(ftp, path, paths)

        return paths

    def get_csvs_parse(self, s, root='https://ftp.ripe.net/rpki', paths=None):

        if paths is None:
            paths = []

        r = s.get(root)
        r.raise_for_status()
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
                #print(os.path.join(root, href))
                self.get_csvs_parse(s, path, paths)

        return paths 

    """
    def reformat_csv(self, csv, path):
        #Replaces commas with tabs, removes URI column,
         #  deletes 'AS' e.g. AS13335 -> 13335,
          # and adds date parsed from the file name.
        with open(csv, 'r+') as f:
            content = f.read().split('\n')[1:]
            # clear the file
            f.seek(0)
            f.truncate()
            for line in content:
                if line:
                    edited_line = line.split(',')[1:]
                    edited_line[0] = edited_line[0][2:]
                    f.write('\t'.join(edited_line))

                    date = '-'.join(path.split('/')[2:5])
                    f.write(f'\t{date}')
                    f.write('\n')
    """ 
