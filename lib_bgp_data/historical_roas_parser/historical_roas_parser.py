#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
from ftplib import FTP, error_perm

from ..base_classes import Parser
from ..utils import utils
from .tables import Historical_ROAS_Table


class Historical_ROAS_Parser(Parser):

    count = 0

    def _run(self):
        # context manager does ftp.quit()
        with FTP('ftp.ripe.net') as ftp:
            ftp.login()
            self.download_csvs(ftp, 'rpki')

    def download_csvs(self, ftp, root):
        for path in ftp.nlst(root):

            # there are 3 possibilities:
            # file is a csv - download and insert into table
            # file is an archive - ignore
            # file is a folder - recurse deeper

            if 'csv' in path:
                csv = 'temp.csv'
                with open(csv, 'wb') as f:
                    ftp.retrbinary(f'RETR {path}', f.write)
                self.reformat_csv(csv)
                utils.csv_to_db(Historical_ROAS_Table, csv)
                self.count += 1
                print(self.count)
            elif 'repo.tar.gz' in path:
                pass
            else:
                self.download_csvs(ftp, path)

    def reformat_csv(self, csv):
        """Replace commas with tabs and remove the first column"""
        with open(csv, 'r+') as f:
            content = f.read()
            # clear everything
            f.seek(0)
            f.truncate()
            for line in content:
                f.write(''.join(line.split(',')[1:]).replace(',', '\t'))
                
                
            
