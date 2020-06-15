#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the ROAs_Automator

The purpose of this class is to parse the roas and insert them into the
database. This class will properly check to see if the database needs to be
restored and will create a backup each time the _run method is called.
"""

__authors__ = ["Samarth Kasbawala"]
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


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
                try:
                    table.clear_table()
                    self._restore_table(table.name)
                except subprocess.CalledProcessError:
                    # Enters this block if there is no compatible backup.
                    # Probably means we haven't created one yet
                    pass
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
                        if self._backup_table(table.name):
                            self._overwrite(table.name)
                            break

                        # If the backup is unsuccessful, restore the table
                        # to the last backup
                        else:
                            try:
                                table.clear_table()
                                self._restore_table(table.name)
                                table.create_index()
                            except subprocess.CalledProcessError:
                                # Enters this block if there is no backup file
                                # to use
                                pass

                    # If after three attempts the backups are unsuccessful,
                    # then just insert the new roas and don't backup.
                    else:
                        utils.clean_paths([self.path, self.csv_dir])
                        utils.rows_to_db(roas, _csv_dir,
                                         ROAs_Table, clear_table=False)
                        table.create_index()

                        # Raise a backup error
                        raise BackupError()

                except (subprocess.CalledProcessError, BackupError):
                    # TODO: Enter this except block if there is an error
                    # creating the backup. Will add functionality so that an
                    # email is sent if the backups fail.
                    pass

########################
### Helper Functions ###
########################

    def _backup_table(self, table_name):
        """This funtion will backup the table and check the backup"""

        # Get the number of rows in the table
        with ROAs_Table() as table:
            count = table.get_count()
            
        # Make a temporary backup
        cmd = (f"sudo -i -u postgres << EOF\n"
               f"pg_dump -Fc -t {table_name} bgp > {table_name}.temp.sql.gz\n"
               f"EOF")
        utils.run_cmds(cmd)

        # Restore the table from the temporary backup we just made
        with ROAs_Table() as table:
            try:
                table.clear_table()
                self._restore_table(table_name, temp=True)
            except:
                # If there are any errors trying to restore the table,
                # the backup was not successful
                return False

        # Get the new count of the table after the restore
        with ROAs_Table() as table:
            restore_count = table.get_count()

        # Return True if the backup is consistent
        return count == restore_count
            
    def _restore_table(self, table_name, temp=False):
        """This function runs the command to restore the table from the
        backup"""

        # Build the bash command
        cmd = "sudo -i -u postgres << EOF\n"
        if temp:
            cmd += f"pg_restore -d bgp {table_name}.temp.sql.gz\n"
        else:
            cmd += f"pg_restore -d bgp {table_name}.sql.gz\n"
        cmd += "EOF"

        utils.run_cmds(cmd)

    def _overwrite(self, table_name):
        cmd = (f"sudo -i -u postgres << EOF\n"
               f"mv {table_name}.temp.sql.gz {table_name}.sql.gz\n"
               f"EOF")
        utils.run_cmds(cmd)

