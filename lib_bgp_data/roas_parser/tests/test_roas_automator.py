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

import os
import pytest
import psycopg2
import subprocess
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

        self.automator.backup_dir = "/nightly_runs/roas_backup/test/"
        self.automator.temp_backup = (f"{self.automator.backup_dir}roas_test"
                                      f"_temp.sql.gz")
        self.automator.prev_backup = (f"{self.automator.backup_dir}roas_test"
                                      f".sql.gz")

        with ROAs_Table() as _roas_table:
            _roas_table.clear_table()

    def teardown(self):
        """Backup files are deleted after each test"""

        subprocess.run(f"rm {self.automator.temp_backup}",
                       capture_output=True,
                       shell=True)
        subprocess.run(f"rm {self.automator.prev_backup}",
                       capture_output=True,
                       shell=True)


    def test__overwrite(self):
        """Tests the _overwrite function"""

        # Assert that a previous and temporary backup files don't exist
        assert os.path.exists(self.automator.prev_backup) is False
        assert os.path.exists(self.automator.temp_backup) is False

        # Create a file that has the name of the temporary backup file
        utils.run_cmds(f"touch {self.automator.temp_backup}")
        assert os.path.exists(self.automator.temp_backup) 

        # Overwrite the previous backup with the temporary one
        self.automator._overwrite()

        # Assert that temporary backup file no longer exits but the previous
        # one does
        assert os.path.exists(self.automator.temp_backup) is False
        assert os.path.exists(self.automator.prev_backup)

    def test__restore_table(self):
        """Tests the _restore_table function

        We use a custom function since the _restore_table and _backup_table
        methods specify the database 'bgp'. Since we are working with the
        'test' database, we simply replace 'bgp' with 'test'.

        The restore function can either restore the table from the temp_backup
        or from the previous backup. Both functionalities are tested.
        """

        # Populate the database using the roas_parser
        self.parser.run()

        with ROAs_Table() as _roas_table:
            # Get the data in the table and make a backup
            roas = _roas_table.get_all()
            self._custom_backup()

            # Drop the table and make sure it doesn't exist
            _roas_table.clear_table()
            with pytest.raises(psycopg2.errors.UndefinedTable):
                _roas_table.get_all()

            # Restore the table into the database
            self._custom_restore(temp=True)
            _roas_table.create_index()
            restored_roas = _roas_table.get_all()

            # Assert that the roas are the same before and after the restore
            assert roas == restored_roas

            # Drop the table and make sure it doesn't exist
            _roas_table.clear_table()
            with pytest.raises(psycopg2.errors.UndefinedTable):
                _roas_table.get_all()

            # Overwrite the prev backup with the temp backup
            self.automator._overwrite()

            # Restore the table and check the contents
            self._custom_restore()
            _roas_table.create_index()

            restored_roas = _roas_table.get_all()
            assert roas == restored_roas


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

        with ROAs_Table(clear=True) as _roas_table:
            with patch(format_path, return_value=formatted_roas) as f_mock, \
                 patch(backup_path) as b_mock, \
                 patch(restore_path) as r_mock:

                b_mock.side_effect = self._custom_backup
                r_mock.side_effect = self._custom_restore

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

        with ROAs_Table(clear=True) as _roas_table:
            with patch(backup_path) as b_mock, \
                 patch(restore_path) as r_mock:

                b_mock.side_effect = self._custom_backup
                r_mock.side_effect = self._custom_restore

                # Get the number of entries in the table, should be 0 at start
                first = _roas_table.get_count()
                assert first == 0

                # Fill the table and check that there are entries in the table
                self.automator.run()
                second = _roas_table.get_count()
                assert first < second

                # Clear the table. We want to see if the restore works in the
                # run function.
                _roas_table.clear_table() 
                with pytest.raises(psycopg2.errors.UndefinedTable):
                    _roas_table.get_all()

                # Insert more roas into the table. If the restore works,
                # there should be more entries after this run call
                self.automator.run()
                third = _roas_table.get_count()
                assert second < third
                assert (third - second) > 100000

    def test_failed_backup(self):
        """This function tests the behavior in case the backup doesn't work"""

        # Patch the backup, restore, and overwrite helper functions
        backup_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_backup_table")
        restore_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                        "_restore_table")

        with ROAs_Table(clear=True) as _roas_table: 
            with patch(restore_path) as r_mock:

                r_mock.side_effect = self._custom_restore

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
                self._custom_restore()

                assert count == _roas_table.get_count()
                assert roas == _roas_table.get_all()

    def test_failed_backup_2(self):
        """Another test to see the behavior of a failed backup

        This test considers the case for when a backup fails and there is no
        previous backup to restore to
        """

        # Get formatted roas
        formatted_roas = self.automator._format_roas(self.automator._get_json_roas())

        # Patch the format, backup, restore, and overwrite functions
        format_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_format_roas")

        # Also want to patch the backup, restore, and overwrite helper 
        # functions because they specify the bgp database. When testing, we
        # are working with test database
        backup_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_backup_table")
        restore_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                        "_restore_table")

        with ROAs_Table(clear=True) as _roas_table:
            with patch(format_path, return_value=formatted_roas) as f_mock, \
                 patch(backup_path, return_value=False) as b_mock, \
                 patch(restore_path) as r_mock:

                r_mock.side_effect = self._custom_restore

                # Parses the roas and inserts them into the database
                self.automator.run()

                # Get the roas from the database and assert the roas match
                assert formatted_roas == [list(row.values())
                                          for row in _roas_table.get_all()]
                assert os.path.exists(self.automator.prev_backup) is False
            
################################
### Patched Helper Functions ###
################################

    def _custom_backup(self):
        """This funtion will backup the table and check the backup"""

        # Get the number of rows in the table
        with ROAs_Table() as table:
            count = table.get_count()

        # Make a temporary backup
        cmd = (f"sudo -i -u postgres "
               f"pg_dump -Fc -t roas test > {self.automator.temp_backup}")
        utils.run_cmds(cmd)

        # Restore the table from the temporary backup we just made
        with ROAs_Table() as table:
            try:
                table.clear_table()
                self._custom_restore(temp=True)
            except:
                # If there are any errors trying to restore the table,
                # the backup was not successful
                return False

        # Get the new count of the table after the restore
        with ROAs_Table() as table:
            restore_count = table.get_count()

        # Return True if the backup is consistent
        return count == restore_count

    def _custom_restore(self, temp=False):
        """This function runs the command to restore the table from the
        backup"""

        cmd = "sudo -i -u postgres "
        if temp:
            cmd += f"pg_restore -d test {self.automator.temp_backup}"
        else:
            cmd += f"pg_restore -d test {self.automator.prev_backup}"
        utils.run_cmds(cmd)

