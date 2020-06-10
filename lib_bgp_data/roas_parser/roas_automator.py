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


class ROAs_Automator(ROAs_Parser):
    def _run(self):
        """Downloads and stores the roas from a json while properly maintaining
        the table in the database
        """

        with ROAs_Table() as _roas_table:

            # Check if the table exists and if it exists, make sure that the
            # table is not empty. If empty or table dne, restore it from the
            # table from the backup. Finally get the new data, store it, and
            # create a new backup
            try:
                count = _roas_table.get_count()
                if count == 0:
                    raise TableIsEmpty()
            except (psycopg2.errors.UndefinedTable, TableIsEmpty):
                try:
                    _roas_table.clear_table()
                    self._restore_table(_roas_table.name)
                except subprocess.CalledProcessError:
                    # Enters this block if there is no compatible backup.
                    # Probably eans we haven't created one yet
                    pass
            finally:
                # Store the roas in database, do not clear the table
                roas = self._format_roas(self._get_json_roas())
                _csv_dir = f"{self.csv_dir}/roas.csv"
                utils.rows_to_db(roas, _csv_dir, ROAs_Table, clear_table=False)
                _roas_table.create_index()

                # Backup the table
                try:
                    self._backup_table(_roas_table.name)
                except subprocess.CalledProcessError:
                    # TODO: Will return an error if backup is not properly
                    # constructed. But I have no idea what could cause this
                    # error since pg_dump is being called with the proper
                    # flags and arguments
                    pass

########################
### Helper Functions ###
########################

    def _backup_table(self, table_name):
        """This function runs the command to backup the roas table"""

        bash = "sudo -i -u postgres << EOF\n"
        bash += f"pg_dump -Fc -t {table_name} bgp > {table_name}.sql.gz\n"
        bash += "EOF"
        utils.run_cmds(bash)

    def _restore_table(self, table_name):
        """This function runs the command to restore the table from the
        backup"""

        bash = "sudo -i -u postgres << EOF\n"
        bash += f"pg_restore -d bgp {table_name}.sql.gz\n"
        bash += "EOF"
        utils.run_cmds(bash)
