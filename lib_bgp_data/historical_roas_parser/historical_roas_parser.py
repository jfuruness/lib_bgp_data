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
#import concurrent.futures
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
        # ProcessPool(nodes=48).map(self.download_csvs)

        # self.download_csvs_test()
        #csv_paths = self.get_csvs()

        self.get_csvs_parse()

        #paths = []
        #with FTP('ftp.ripe.net') as ftp:
        #    ftp.login()
        #    print(self.get_csvs(ftp, 'rpki'))

           
        # context manager does ftp.quit()
        #with FTP('ftp.ripe.net') as ftp:
         #   ftp.login()
          #  with Historical_ROAS_Table() as db:
           #     self.download_csvs(ftp, 'rpki', db)
            #    db.create_index()

    def download_csv(self, path):
        with open('temp.csv', 'wb') as f:
            path[1].retrbinary(f'RETR {path[0]}', f.write())
            self.reformat_csv(csv_path)
        with Historical_ROAS_Parsed_Table() as db:
            db.execute(f"INSERT INTO {db.name}(file) VALUES ({path})")

    """
    def download_csvs(self, ftp, root, db, paths):
        for path in ftp.nlst(root):

            # there are 3 possibilities:i
            # file is a csv - download and insert into table
            # file is an archive - ignore
            # file is a folder - recurse deeper

            if 'csv' in path:
                paths.append(path)

                with Historical_ROAS_Parsed_Table() as parsed:
                    sql = f"SELECT * FROM {parsed.name} WHERE file = {path}" 
                    if not parsed.get_count(sql=sql):
                    csv = 'temp.csv'
                    with open(csv, 'wb') as f:
                        ftp.retrbinary(f'RETR {path}', f.write)
                        self.reformat_csv(csv, path)
                        utils.csv_to_db(Historical_ROAS_Table, csv)
                        self.count += 1
                        print(self.count, path)
                        db.delete_duplicates()

            elif 'repo.tar.gz' in path:
                pass

            else:
                self.download_csvs(ftp, path, db)
    """

    def download_csvs_test(self):

        # wget all the csv files - 2 hrs
        p = subprocess.run('wget -r -np -e robots=off -A "*.csv" ftp.ripe.net/rpki/',
            shell=True)

        # list the paths to each csv
        output = subprocess.run(f'find {os.getcwd()} -type f',
                            shell=True, capture_output=True)
        print(output.stdout)

    def wget_try(self):
        check_call('wget -r -np -R "repo.tar.gz" ftp.ripe.net/rpki/', shell=True)

    def get_csvs(self, ftp, root, paths=None):
        if paths is None:
            paths = []
        print(len(paths))
        if len(paths) == 50:
            return
        for path in ftp.nlst(root):
            print(path)
            if 'csv' in path:
                paths.append(path)
            elif 'repo.tar.gz' in path:
                pass
            else:
                self.get_csvs(ftp, path, paths)
        return paths

    def get_csvs_parse(self, root='https://ftp.ripe.net/rpki'):

        r = requests.get(root)
        r.raise_for_status()
        s = Soup(r.text, 'lxml')
        r.close()

        # the first link is the parent directory
        for link in s('a')[1:]:
            href = link['href']
            if href == '/' or href == 'repo.tar.gz':
                pass
            elif 'csv' in href:
                subprocess.run(f'wget {root}', shell=True)
                print('Downloaded something')
                # maybe then do the reformating and insertion here
            else:
                #print(os.path.join(root, href))
                self.get_csvs_parse(os.path.join(root, href))

    def reformat_csv(self, csv, path):
        """Replaces commas with tabs, removes URI column,
           deletes 'AS' e.g. AS13335 -> 13335,
           and adds date parsed from the file name."""
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
 
            
