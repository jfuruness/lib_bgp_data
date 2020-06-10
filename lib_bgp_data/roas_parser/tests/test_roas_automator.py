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
        """Backup file is deleted after each test"""

        utils.run_cmds("sudo -i -u postgres rm roas_test.sql.gz")

    def test__restore_table(self):
        """Tests the _restore_table function

        We use a custom function since the _restore_table and _backup_table
        methods specify the database 'bgp'. Since we are working with the
        'test' database, we simply replace 'bgp' with 'test'.
        """

        # Populate the database
        self.parser.run()

        with ROAs_Table() as _roas_table:

            # Get the data in the table and make a backup
            roas = _roas_table.get_all()
            self._custom_backup(_roas_table.name)

            # Drop the table and make sure it doesn't exist
            _roas_table.clear_table()
            with pytest.raises(psycopg2.errors.UndefinedTable):
                _roas_table.get_all()

            # Restore the table into the database
            self._custom_restore(_roas_table.name)
            _roas_table.create_index()
            restored_roas = _roas_table.get_all()

            # Assert that the roas are the same before and after the restore
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

        # Also want to patch the backup and restore helper functions because
        # they specify the bgp database. When testing, we are working with
        # test database
        backup_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_backup_table")
        restore_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                        "_restore_table")

        with patch(format_path, return_value=formatted_roas) as f_mock, \
             patch(backup_path) as b_mock, \
             patch(restore_path) as r_mock:

            b_mock.side_effect = self._custom_backup
            r_mock.side_effect = self._custom_restore

            # Parses the roas and inserts them into the database
            self.automator.run()

            # Get the roas from the database and assert the roas match
            with ROAs_Table() as db:
                assert formatted_roas == [list(row.values())
                                          for row in db.get_all()]

    def test_successive_runs(self):
        """Tests for successive insertions into the table"""
 
        with ROAs_Table() as db:

            backup_path = ("lib_bgp_data.roas_parser.roas_automator."
                           "ROAs_Automator._backup_table")
            restore_path = ("lib_bgp_data.roas_parser.roas_automator."
                            "ROAs_Automator._restore_table")

            with patch(backup_path) as b_mock, patch(restore_path) as r_mock:
                b_mock.side_effect = self._custom_backup
                r_mock.side_effect = self._custom_restore

                first = db.get_count()
                self.automator._run()
                second = db.get_count()
                utils.clean_paths([self.automator.path,
                                   self.automator.csv_dir])
                self.automator._run()
                third = db.get_count()
                assert first < second < third

########################
### Helper Functions ###
########################

    def _custom_backup(self, table_name):
        bash = "sudo -i -u postgres << EOF\n"
        bash += f"pg_dump -Fc -t {table_name} test > {table_name}_test.sql.gz\n"
        bash += "EOF"
        utils.run_cmds(bash)

    def _custom_restore(self, table_name):
        bash = "sudo -i -u postgres << EOF\n"
        bash += f"pg_restore -d test {table_name}_test.sql.gz\n"
        bash += "EOF"
        utils.run_cmds(bash)
