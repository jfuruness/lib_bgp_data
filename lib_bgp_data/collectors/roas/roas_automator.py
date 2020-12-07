#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the ROAs_Automator

The purpose of this class is to parse the roas and insert them into the
database. This class will properly check to see if the database needs to be
restored and will create a backup each time the _run method is called.

First, the roas table in the database is checked. If this table is empty or
dne, the table will be restored from a previous backup. If there is no
previous backup, new data will be inserted using an emppty table.

Next, the roas json is retrieved. The new data is inserted and a new backup is
made. The table is then restored from the is backup. If number of rows in the
table is the same after the insertion and then after the restore, the previous
backup is overwritten. If the tempporary backup doesn't contain the same amount
of data, we try creating a backup again. We try to make a backup at most three
times. If a backup cannot be made for some reason, we do not overwrite the
previous backup.

If the backup fails, an email will be sent, notifying the user of any errors
if pg_dump or pg_restore have any.

This automator is designed to be run nightly on our server using cron.
"""


__authors__ = ["Samarth Kasbawala"]
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import os
import psycopg2
import pytest
import subprocess

from .tables import ROAs_Table
from .roas_parser import ROAs_Parser
from ...utils.base_classes import Parser
from ...utils import utils


class TableIsEmpty(Exception):
    pass


class BackupError(Exception):
    pass


class ROAs_Automator(ROAs_Parser):
    """ROAs_AUtomator class"""

    # Define backup directories and make sure they exist
    backup_dir = "/nightly_runs/roas_backup"
    temp_backup = os.path.join(backup_dir, "roas_temp.sql.gz")
    prev_backup = os.path.join(backup_dir, "roas.sql.gz")
 
    def _run(self):
        """Downloads and stores the roas from a json while properly maintaining
        the table in the database
        """

        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)


        from ..database.config import global_section_header as gsh
        assert gsh is not None

        with ROAs_Table() as table:

            # Check if the table exists and if it exists, make sure that the
            # table is not empty. If empty or table dne, restore it from the
            # table from the backup. Finally get the new data, store it, and
            # create a new backup
            try:
                count = table.get_count()
                if count == 0:
                    raise TableIsEmpty()
            except (psycopg2.errors.UndefinedTable, TableIsEmpty):
                if os.path.exists(self.prev_backup):
                    table.clear_table()
                    table.restore_table(gsh, self.prev_backup)
                    table.create_index()
            finally:
                # Get the roas that need to be inserted into the table
                roas = self._format_roas(self._get_json_roas())
                _csv_dir = f"{self.csv_dir}/roas.csv"

                # Try backing up the table at most three times. If
                # unsuccessful, send an email indicating the error
                try:
                    self._try_to_backup(roas, _csv_dir, table)
                except (subprocess.CalledProcessError, BackupError) as e:
                    if not pytest.global_running_test:
                        subject = f"Roas Backup Error at {utils.now()}"
                        if type(e) == BackupError:
                            body = ("There was an error backing up the roas table. "
                                    "The backup file was not created correctly, so "
                                    "the previous backup was not overwritten. The "
                                    "pg_dump and pg_restore commands did not provide "
                                    "an error.")
                        else:
                            body = ("There was an error backing up the roas table. "
                                    "Below are the outputs\n"
                                    f"STD_OUT Message: {e.stdout}\n"
                                    f"STD_ERR Message: {e.stderr}")
                        utils.send_email(subject, body)

########################
### Helper Functions ###
########################

    def _try_to_backup(self, roas, csv_dir, table):
        """Tries to backup table at most three times"""

        from ..database.config import global_section_header as gsh
        assert gsh is not None

        for _ in range(3):
            # Insert the roas into the table
            self._insert_rows(roas, csv_dir, table)

            # Create a backup, if it is successful, overwrite the
            # existing backup
            table.backup_table(table.name, gsh, self.temp_backup)
            if self._check_backup(table):
                self._overwrite()
                break

            # If the backup is unsuccessful, restore the table
            # to the last backup
            if os.path.exists(self.prev_backup):
                table.clear_table()
                table.restore_table(gsh, self.prev_backup)
                table.create_index()

            # Enters this block if there is no previous backup,
            # need to make the table empty so that data can tried
            # to be inserted again
            else:
                table.execute(f"DELETE FROM {table.name}")
                
        # If after three attempts the backups are unsuccessful,
        # then just insert the new roas and don't backup.
        else:
            self._insert_rows(roas, csv_dir, table)
            raise BackupError()

    def _insert_rows(self, roas, csv_dir, table):
        """Inserts roas into table"""

        utils.clean_paths([self.path, self.csv_dir])
        utils.rows_to_db(roas, csv_dir, ROAs_Table, clear_table=False)
        table.create_index()

    def _check_backup(self, table):
        """Checks whether or not the backup failed and returns a boolean"""

        from ..database.config import global_section_header as gsh
        assert gsh is not None

        count = table.get_count()

        try:
            table.clear_table()
            table.restore_table(gsh, self.temp_backup)
            table.create_index()
        except:
            return False
        else:
            return count == table.get_count()

    def _overwrite(self):
        """This function overwrites the previous backup"""

        cmd = f"mv {self.temp_backup} {self.prev_backup}"
        utils.run_cmds(cmd)

