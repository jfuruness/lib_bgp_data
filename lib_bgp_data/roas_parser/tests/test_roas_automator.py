#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the roas_automator.py file

For specifics on each test see the docstrings under each function. Note that
the _backup_table function is not tested since we can only test its
functionality by restoring from the backup.
"""

__authors__ = ["Samarth Kasbawala"]
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
import psycopg2
import subprocess
import time
from unittest.mock import Mock, patch

from ..roas_parser import ROAs_Parser
from ..roas_automator import ROAs_Automator
from ..tables import ROAs_Table
from ...utils import utils


@pytest.mark.roas_parser
class Test_ROAs_Automator:
    """Tests all functions within the ROAs_Automator class"""

    def setup(self):
        """Parser and automator setup and table deleted before every test"""

        self.parser = ROAs_Parser()
        self.automator = ROAs_Automator()
        with ROAs_Table() as _roas_table:
            _roas_table.clear_table()

    def teardown(self):
        """Backup files are deleted after each test"""

        subprocess.run("sudo -i -u postgres rm roas_test.temp.sql.gz",
                       capture_output=True,
                       shell=True)
        subprocess.run("sudo -i -u postgres rm roas_test.sql.gz",
                       capture_output=True,
                       shell=True)

    def test__restore_table(self):
        """Tests the _restore_table function

        We use a custom function since the _restore_table and _backup_table
        methods specify the database 'bgp'. Since we are working with the
        'test' database, we simply replace 'bgp' with 'test'. The backup
        function already has its own built in check, however it is still a
        good idea to explicitly check.
        """

        # Populate the database
        self.parser.run()

        with ROAs_Table() as _roas_table:
            # Get the data in the table and make a backup
            roas = _roas_table.get_all()
            status = self._custom_backup(_roas_table.name)

            # Drop the table and make sure it doesn't exist
            _roas_table.clear_table()
            with pytest.raises(psycopg2.errors.UndefinedTable):
                _roas_table.get_all()

            # Restore the table into the database
            self._custom_restore(_roas_table.name, temp=True)
            _roas_table.create_index()
            restored_roas = _roas_table.get_all()

            # Assert that the roas are the same before and after the restore
            assert roas == restored_roas

    def test__overwrite(self):
        utils.run_cmds("sudo -i -u postgres touch roas_test.temp.sql.gz") 
        self._custom_overwrite("roas")
        with pytest.raises(subprocess.CalledProcessError):
            utils.run_cmds("sudo -i -u postgres ls roas_test.temp.sql.gz")  
        utils.run_cmds("sudo -i -u postgres ls roas_test.sql.gz") 

    def test__run(self):
        """Tests the _run function in the ROAs_Automator class"""

        # Get formatted roas
        formatted_roas = self.automator._format_roas(self.automator._get_json_roas())

        # Patch the format roas function in the _run function because we want
        # to have consistent time stamps. Every time the format roas function
        # is run, the timestamps for each row will change
        format_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_format_roas")

        # Also want to patch the backup, restore, and overwrite helper 
        # functions because they specify the bgp database. When testing, we
        # are working with test database
        backup_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_backup_table")
        restore_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                        "_restore_table")
        overwrite_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                          "_overwrite")

        with ROAs_Table(clear=True) as _roas_table:
            with patch(format_path, return_value=formatted_roas) as f_mock, \
                 patch(backup_path) as b_mock, \
                 patch(restore_path) as r_mock, \
                 patch(overwrite_path) as o_mock:

                b_mock.side_effect = self._custom_backup
                r_mock.side_effect = self._custom_restore
                o_mock.side_effect = self._custom_overwrite

                # Parses the roas and inserts them into the database
                self.automator.run()

                # Get the roas from the database and assert the roas match
                assert formatted_roas == [list(row.values())
                                          for row in _roas_table.get_all()]

    def test_successive_runs(self):
        """Tests for successive insertions into the table"""
    
        # Patch the backup, restore, and overwrite helper functions
        backup_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_backup_table")
        restore_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                        "_restore_table")
        overwrite_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                          "_overwrite")

        with ROAs_Table(clear=True) as _roas_table:
            with patch(backup_path) as b_mock, \
                 patch(restore_path) as r_mock, \
                 patch(overwrite_path) as o_mock:

                b_mock.side_effect = self._custom_backup
                r_mock.side_effect = self._custom_restore
                o_mock.side_effect = self._custom_overwrite

                # Get the number of entries in the table, should be 0 at start
                first = _roas_table.get_count()
                assert first == 0

                # Fill teh table and check that there are entries in the table
                self.automator.run()
                second = _roas_table.get_count()
                assert first < second

                # Clear the table.We want to see if the restore works in the
                # run function.
                _roas_table.clear_table() 
                with pytest.raises(psycopg2.errors.UndefinedTable):
                    _roas_table.get_all()

                # Insert more roas into the table. If the restore works,
                # there should be more entries after this run call
                self.automator.run()
                third = _roas_table.get_count()
                assert second < third
                assert (third - second) > 10000

    def test_failed_backup(self):
        """This function tests the behavior in case the backup doesn't work"""

        # Patch the backup, restore, and overwrite helper functions
        backup_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_backup_table")
        restore_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                        "_restore_table")
        overwrite_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                          "_overwrite")

        with ROAs_Table(clear=True) as _roas_table: 
            with patch(restore_path) as r_mock, \
                 patch(overwrite_path) as o_mock:

                r_mock.side_effect = self._custom_restore
                o_mock.side_effect = self._custom_overwrite

                with patch(backup_path) as b_mock:
                    # Fill the table creating a backup normally, a backup file
                    # should be made after run is called
                    b_mock.side_effect = self._custom_backup
                    self.automator.run()

                # Get the roas that have been inserted into the table
                roas = _roas_table.get_all()
                count = _roas_table.get_count()

                # Patch the backup function so that it fails
                with patch(backup_path, return_value=False) as b_mock:
                    # Run the automator again
                    self.automator.run()

                # Assert that new data was added
                assert count < _roas_table.get_count()

                # Suppose the table gets cleared, restoring from the last
                # backup would not contain the data from the second call
                _roas_table.clear_table()
                self._custom_restore(_roas_table.name)

                assert count == _roas_table.get_count()
                assert roas == _roas_table.get_all() 
            
################################
### Patched Helper Functions ###
################################

    def _custom_backup(self, table_name):
        """This funtion will backup the table and check the backup"""

        # Get the number of rows in the table
        with ROAs_Table() as table:
            count = table.get_count()

        # Make a temporary backup
        cmd = (f"sudo -i -u postgres << EOF\n"
               f"pg_dump -Fc -t {table_name} test > {table_name}_test.temp.sql.gz\n"
               f"EOF")
        utils.run_cmds(cmd)

        # Restore the table from the temporary backup we just made
        with ROAs_Table() as table:
            try:
                table.clear_table()
                self._custom_restore(table_name, temp=True)
            except:
                # If there are any errors trying to restore the table,
                # the backup was not successful
                return False

        # Get the new count of the table after the restore
        with ROAs_Table() as table:
            restore_count = table.get_count()

        # Return True if the backup is consistent
        return count == restore_count

    def _custom_restore(self, table_name, temp=False):
        """This function runs the command to restore the table from the
        backup"""

        # Build the bash command
        cmd = "sudo -i -u postgres << EOF\n"
        if temp:
            cmd += f"pg_restore -d test {table_name}_test.temp.sql.gz\n"
        else:
            cmd += f"pg_restore -d test {table_name}_test.sql.gz\n"
        cmd += "EOF"

        utils.run_cmds(cmd)

    def _custom_overwrite(self, table_name):
        cmd = (f"sudo -i -u postgres << EOF\n"
               f"mv {table_name}_test.temp.sql.gz {table_name}_test.sql.gz\n"
               f"EOF")
        utils.run_cmds(cmd)

