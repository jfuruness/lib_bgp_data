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
import concurrent.futures

from ..base_classes import Parser
from ..utils import utils
from .tables import Historical_ROAS_Table, Historical_ROAS_Parsed_Table


class Historical_ROAS_Parser(Parser):

    count = 0

    def _run(self):
        """Collect the paths to all the csvs to download. Multithread the
           downloading of all the csvs, insert into db if not seen before."""

        paths = []
        with FTP('ftp.ripe.net') as ftp:
            ftp.login()
            self.get_csvs(ftp, 'rpki', paths)
            paths = [(p, ftp) for p in paths]

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.download_csv, paths)
           
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

            # there are 3 possibilities:
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

    def get_csvs(self, ftp, root, paths):
        for path in ftp.nlst(root):
            if 'csv' in path:
                paths.append(path)
            elif 'repo.tar.gx' in path:
                pass
            else:
                self.get_csvs(ftp, path, paths)

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
 
            
