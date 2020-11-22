#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a script to run BGPStream_Website_Parser, backup, and restore if 
necessary.

First, the database is checked for the hijacks, leaks, and outages tables.
If any of those tables don't exist or are empty, they will be restored from
the previous backup.

Second, the BGPStream_Website_Parser is run. A backup is made after the run.
If the backup contains more data than the previous backup, the previous
backup is overwritten.

To schedule this to run on our server nightly at 4 AM using cron:

Edit cron jobs by running this command:
sudo crontab -e

Then add this line:
0 4 * * * /nightly_runs/env/bin/lib_bgp_data --bgpstream_website_runner

For reconfiguring cron, this is a useful article:
https://medium.com/@gavinwiener/how-to-schedule-a-python-script-cron-job-dea6cbf69f4e

In addition, an email is sent if the runner restores a table and it is still
somehow empty. Either the restore process could have failed, or the backup
file is somehow corrupted. Please check the the backup and the database in
such a situation.
"""

import os
from subprocess import check_call

import psycopg2

from ..base_classes import Parser
from ...utils import utils
from .bgpstream_website_parser import BGPStream_Website_Parser
from .tables import Hijacks_Table, Leaks_Table, Outages_Table

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class BGPStream_Website_Runner(Parser):
    table_list = [Hijacks_Table, Leaks_Table, Outages_Table]
    backup_dir = '/nightly_runs/bgpstream_backup/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.section = self.kwargs['section']

    def _run(self):
        try:
            for table in self.table_list:
                backup = f'{table.name}.sql.gz'
                with table() as t:
                    try:
                        count = t.get_count()
                    except psycopg2.errors.UndefinedTable:
                        self.restore(backup, t)

                    if count == 0:
                        self.restore(backup, t)

            BGPStream_Website_Parser()._run()
            for table in self.table_list:
                self.backup(table)

        except AssertionError:
            subject = f'[{utils.now()}] BGPStream_Website_Parser Error'
            body = ('Nightly run of BGPStream_Website_parser failed. '
                    'Either restoring failed or a backup is corrupted. '
                    'Please check the backups and the live db.')
            utils.send_email(subject, body)

    def backup(self, table):
        """Makes a new backup if live table has more data than old backup."""

        prev_backup = os.path.join(self.backup_dir, f'{table.name}.sql.gz')
        tmp_backup = os.path.join(self.backup_dir, 'temp.sql.gz')
       
        # making the backup directory if doesn't exist. (e.g. first time)
        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)

        # if previous backups don't exists, make backups right now
        if not os.path.exists(prev_backup):
            self.pg_cmd(f'pg_dump -Fc -t {table.name} '
                        f'{self.section} > {prev_backup}')
 
        # make a temp backup of live table
        self.pg_cmd(f'pg_dump -Fc -t {table.name} '
                    f'{self.section} > {tmp_backup}')

        with table() as db:
            # copy live table
            db.execute('DROP TABLE IF EXISTS temp')
            db.execute(f'CREATE TABLE temp AS TABLE {table.name}')

            # restore previous backup
            self.restore(prev_backup, db)
            count_prev = db.get_count()
            
            # restore temp
            self.restore(tmp_backup, db)
            count_tmp = db.get_count()

            # new backup is larger, save as the most up-to-date backup
            if count_tmp > count_prev:
                check_call(f'mv {tmp_backup} {prev_backup}', shell=True)
            # restore live table
            db.execute(f'DROP TABLE {table.name}')
            db.execute(f'CREATE TABLE {table.name} AS TABLE temp')
            db.execute('DROP TABLE temp')

            if os.path.exists(tmp_backup):
                os.remove(tmp_backup)

    def restore(self, backup, table):
        """Restores backup into clean table, then checks table is nonempty."""

        self.pg_cmd(f'pg_restore -c --if-exists -d {self.section} {backup}')
         
        assert table.get_count() > 0, ('Table is still empty. '
                                       'Restore or backup must have failed.') 

    def pg_cmd(self, cmd: str):
        """executes cmd as postgres user"""
        check_call(f'sudo -i -u postgres {cmd}', shell=True)

