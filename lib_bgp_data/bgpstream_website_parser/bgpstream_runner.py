#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import os
from subprocess import check_call

import psycopg2

from lib_bgp_data.bgpstream_website_parser.bgpstream_website_parser import BGPStream_Website_Parser
from lib_bgp_data.bgpstream_website_parser.tables import Hijacks_Table, Leaks_Table, Outages_Table

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Runner:
    table_list = [Hijacks_Table, Leaks_Table, Outages_Table]
    backup_dir = '/ext/lib_bgp_data/lib_bgp_data/bgpstream_website_parser/backups/'

    def run(self):
        print("I'm running")
        for table in self.table_list:
            backup = f'{table.name}.sql.gz'
            with table() as t:
                try:
                    count = t.get_count()
                except psycopg2.errors.UndefinedTable:
                    print('something wrong had to restore')
                    self.restore(backup)
            if count == 0:
                print('something wrong had to restore')
                self.restore(backup)

        BGPStream_Website_Parser().run()
        for table in self.table_list:
            print(f'backing up {table.name}')
            self.backup(table)

    def backup(self, table):
        prev_backup = f'{self.backup_dir}{table.name}.sql.gz'
        tmp_backup = f'{self.backup_dir}temp.sql.gz'
       
        # this is actually the first time backing up
        if not os.path.exists(prev_backup):
            self.pg_cmd(f'pg_dump -Fc -t {table.name} bgp > {prev_backup}')
 
        # make a temp backup of live table
        self.pg_cmd(f'pg_dump -Fc -t {table.name} bgp > {tmp_backup}')

        with table() as db:
            # copy live table
            db.execute('DROP TABLE IF EXISTS temp')
            db.execute(f'CREATE TABLE temp AS TABLE {table.name}')

            # restore previous backup
            self.restore(prev_backup)
            count_prev = db.get_count()
            
            # restore temp
            self.restore(tmp_backup)
            count_tmp = db.get_count()

            # new backup is larger, save as the most up-to-date backup
            if count_tmp > count_prev:
                self.pg_cmd(f'mv {tmp_backup} {prev_backup}')

            # restore live table
            db.execute(f'DROP TABLE {table.name}')
            db.execute(f'CREATE TABLE {table.name} AS TABLE temp')
            db.execute('DROP TABLE temp')

    def restore(self, backup):
        self.pg_cmd(f'pg_restore -c --if-exists -d bgp {backup}')

    def pg_cmd(self, cmd: str):
        check_call(f'sudo -i -u postgres {cmd}', shell=True)

 
if __name__=='__main__':
    Runner().run()


