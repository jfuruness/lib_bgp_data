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

This automator is designed to be run nightly on our server using cron.

FEATURE TO ADD: Upon a failed backup, the script will send an email detailing
the error.
"""

__authors__ = ["Samarth Kasbawala"]
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
import psycopg2
import subprocess
from .tables import ROAs_Table
from .roas_parser import ROAs_Parser
from ..base_classes import Parser
from ..utils import utils


class TableIsEmpty(Exception):
    pass

class BackupError(Exception):
    pass

class ROAs_Automator(ROAs_Parser):
    backup_dir = "/nightly_runs/roas_backup/"
    temp_backup = f"{backup_dir}roas_temp.sql.gz"
    prev_backup = f"{backup_dir}roas.sql.gz"
 
    def _run(self):
        """Downloads and stores the roas from a json while properly maintaining
        the table in the database
        """

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
                    self._restore_table()
                    table.create_index()
            finally:
                # Get the roas that need to be inserted into the table
                roas = self._format_roas(self._get_json_roas())
                _csv_dir = f"{self.csv_dir}/roas.csv"

                # Try backing up the table at most three times
                try:
                    for _ in range(3):
                        # Insert the rows into the table
                        utils.clean_paths([self.path, self.csv_dir])
                        utils.rows_to_db(roas, _csv_dir,
                                         ROAs_Table, clear_table=False)
                        table.create_index()

                        # Create a backup, if it is successful, overwrite the
                        # existing backup
                        if self._backup_table():
                            self._overwrite()
                            break

                        # If the backup is unsuccessful, restore the table
                        # to the last backup
                        if os.path.exists(self.prev_backup):
                            table.clear_table()
                            self._restore_table()
                            table.create_index()

                        # Enters this block if there is no previous backup,
                        # need to make the table empty so that data can tried
                        # to be inserted again
                        else:
                            table.execute("DELETE FROM roas")
                            
                    # If after three attempts the backups are unsuccessful,
                    # then just insert the new roas and don't backup.
                    else:
                        utils.clean_paths([self.path, self.csv_dir])
                        utils.rows_to_db(roas, _csv_dir,
                                         ROAs_Table, clear_table=False)
                        table.create_index()

                        # Raise a backup error
                        raise BackupError()

                except subprocess.CalledProcessError as e:
                    time = utils.now()
                    subject = f"Roas Backup Error at {time}"
                    body = ("There was an error backing up the roas table. "
                            "Below are the outputs\n"
                            f"STD_OUT Message: {e.stdout}\n"
                            f"STD_ERR Message: {e.stderr}")
                    utils.send_email(subject, body)

                except BackupError:
                    time = utils.now()
                    subject = f"Roas Backup Error at {time}"
                    body = ("There was an error backing up the roas table. "
                            "The backup file was not created correctly, so "
                            "the previous backup was not overwritten. The "
                            "pg_dump and pg_restore commands did not provide "
                            "an error.")
                    utils.send_email(subject, body)

########################
### Helper Functions ###
########################

    def _backup_table(self):
        """This funtion will backup the table and check the backup"""

        # Get the number of rows in the table
        with ROAs_Table() as table:
            count = table.get_count()
            
        # Make a temporary backup
        cmd = (f"sudo -i -u postgres "
               f"pg_dump -Fc -t roas bgp > {self.temp_backup}")
        subprocess.run(cmd, check=True, capture_output=True,
                       shell=True, text=True)

        # Restore the table from the temporary backup we just made
        with ROAs_Table() as table:
            try:
                table.clear_table()
                self._restore_table(temp=True)
                table.create_index()
            except:
                # If there are any errors trying to restore the table,
                # the backup was not successful
                return False

        # Get the new count of the table after the restore
        with ROAs_Table() as table:
            restore_count = table.get_count()

        # Return True if the backup is consistent
        return count == restore_count
            
    def _restore_table(self, temp=False):
        """This function runs the command to restore the table from the
        backup"""

        cmd = "sudo -i -u postgres "
        if temp:
            cmd += f"pg_restore -d bgp {self.temp_backup}"
        else:
            cmd += f"pg_restore -d bgp {self.prev_backup}"
        subprocess.run(cmd, check=True, capture_output=True,
                       shell=True, text=True) 

    def _overwrite(self):
        """This function overwrites the previous backup"""

        cmd = f"mv {self.temp_backup} {self.prev_backup}"
        subprocess.run(cmd, check=True, capture_output=True,
                       shell=True, text=True) 

