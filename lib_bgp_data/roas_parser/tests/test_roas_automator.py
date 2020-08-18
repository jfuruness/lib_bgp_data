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
from ...database import Database


@pytest.mark.roas_parser
class Test_ROAs_Automator:
    """Tests all functions within the ROAs_Automator class"""

    @classmethod
    def setup_class(cls):
        """Get roas so they don't have to be retrieved for every test"""

        cls.automator = ROAs_Automator()
        cls.formatted_roas = cls.automator._format_roas(cls.automator._get_json_roas())
        
    def setup_method(self, method):
        """Parser and automator setup and table deleted before every test"""

        self.automator.backup_dir = "/nightly_runs/roas_backup/test"
        if not os.path.exists(self.automator.backup_dir):
            os.mkdir(self.automator.backup_dir)
        self.automator.temp_backup = os.path.join(self.automator.backup_dir,
                                                  "roas_test_temp.sql.gz")
        self.automator.prev_backup = os.path.join(self.automator.backup_dir,
                                                  "roas_test.sql.gz")

        with Database() as _db:
            _db.execute("DROP TABLE IF EXISTS roas;")

    def teardown_method(self, method):
        """Backup files are deleted after each test"""

        utils.delete_paths([self.automator.temp_backup,
                            self.automator.prev_backup])

    def test__overwrite(self):
        """Tests the _overwrite function"""

        # Assert that previous and temporary backup files don't exist
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


    def test__insert_rows(self):
        """Tests the _insert_rows function in the ROAs_Automator class"""

        assert os.path.exists(self.automator.prev_backup) is False
        assert os.path.exists(self.automator.temp_backup) is False

        _csv_dir = f"{self.automator.csv_dir}/roas.csv"

        with ROAs_Table() as _roas_table:
            assert _roas_table.get_count() == 0
            self.automator._insert_rows(self.formatted_roas, _csv_dir, _roas_table)
            assert _roas_table.get_count() > 100000
            assert self.formatted_roas == [list(row.values())
                                           for row in _roas_table.get_all()]

    def test__check_backup(self):
        """Tests the _check_backup function in the ROAs_Automator class"""

        assert os.path.exists(self.automator.prev_backup) is False
        assert os.path.exists(self.automator.temp_backup) is False

        _csv_dir = f"{self.automator.csv_dir}/roas.csv"
        
        with ROAs_Table() as _roas_table:
            self.automator._insert_rows(self.formatted_roas, _csv_dir, _roas_table)
            _roas_table.backup_table(_roas_table.name, 'test', self.automator.temp_backup)
            assert os.path.exists(self.automator.temp_backup)
            assert self.automator._check_backup(_roas_table)
            assert self.formatted_roas == [list(row.values())
                                           for row in _roas_table.get_all()]

    def test__try_to_backup(self):
        """Test the _try_to_backup function in the ROAs_Automator class"""

        assert os.path.exists(self.automator.prev_backup) is False
        assert os.path.exists(self.automator.temp_backup) is False

        _csv_dir = f"{self.automator.csv_dir}/roas.csv"

        with ROAs_Table() as _roas_table:
            assert _roas_table.get_count() == 0
            self.automator._try_to_backup(self.formatted_roas,
                                          _csv_dir,
                                          _roas_table)
            assert _roas_table.get_count() > 100000
            assert os.path.exists(self.automator.prev_backup)
            assert os.path.exists(self.automator.temp_backup) is False
                
        
    def test__run(self):
        """Tests the _run function in the ROAs_Automator class"""

        # Patch the format roas function in the _run function because we want
        # to have consistent time stamps. Every time the format roas function
        # is run, the timestamps for each row will change
        format_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_format_roas")

        with ROAs_Table() as _roas_table:
            with patch(format_path, return_value=self.formatted_roas) as f_mock:

                # Parses the roas and inserts them into the database
                self.automator.run()

                # Make sure backup file was made
                assert os.path.exists(self.automator.prev_backup)
                assert os.path.exists(self.automator.temp_backup) is False

                # Get the roas from the database and assert the roas match
                assert self.formatted_roas == [list(row.values())
                                               for row in _roas_table.get_all()]

    def test_successive_runs(self):
        """Tests for successive insertions into the table"""

        assert os.path.exists(self.automator.prev_backup) is False
        assert os.path.exists(self.automator.temp_backup) is False
 
        with ROAs_Table() as _roas_table:

            # Get the number of entries in the table, should be 0 at start
            first = _roas_table.get_count()
            assert first == 0

            # Fill the table and check that there are entries in the table
            self.automator.run()
            second = _roas_table.get_count()
            assert first < second
            assert os.path.exists(self.automator.prev_backup)
            assert os.path.exists(self.automator.temp_backup) is False

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
            assert os.path.exists(self.automator.prev_backup)
            assert os.path.exists(self.automator.temp_backup) is False

    # Test is off because we don't want to send an email
    def OFFtest_failed_backup(self):
        """This function tests the behavior in case the backup doesn't work

        An email should be sent indicating there was an error backing up the
        table.
        """

        # Check backup method path
        check_backup_path = ("lib_bgp_data.roas_parser.roas_automator."
                             "ROAs_Automator._check_backup")

        with ROAs_Table() as _roas_table: 
            # Fill the table creating a backup normally, a backup file
            # should be made after run is called
            self.automator.run()

            assert os.path.exists(self.automator.prev_backup)
            assert os.path.exists(self.automator.temp_backup) is False

            # Get the roas that have been inserted into the table
            roas = _roas_table.get_all()
            count = _roas_table.get_count()

            # Patch the backup function so that it fails, run automator
            with patch(check_backup_path, return_value=False) as cb_mock:
                self.automator.run()

            # Assert that new data was added
            assert count < _roas_table.get_count()

            # Suppose the table gets cleared, restoring from the last
            # backup would not contain the data from the second call
            _roas_table.clear_table()
            _roas_table.restore_table('test', self.automator.prev_backup)
            _roas_table.create_index()
            
            assert count == _roas_table.get_count()
            assert roas == _roas_table.get_all()

    # Test is off because we don't want to send an email
    def OFFtest_failed_backup_2(self):
        """Another test to see the behavior of a failed backup

        This test considers the case for when a backup fails and there is no
        previous backup to restore to. An email should be sent indicating there
        was an error backing up the table.
        """

        format_path = ("lib_bgp_data.roas_parser.roas_automator.ROAs_Automator."
                       "_format_roas")
        check_backup_path = ("lib_bgp_data.roas_parser.roas_automator."
                             "ROAs_Automator._check_backup")

        with ROAs_Table() as _roas_table:
            with patch(format_path, return_value=self.formatted_roas) as f_mock, \
                 patch(check_backup_path, return_value=False) as cb_mock:

                # Parses the roas and inserts them into the database
                self.automator.run()

                # Get the roas from the database and assert the roas match
                assert self.formatted_roas == [list(row.values())
                                               for row in _roas_table.get_all()]
                assert os.path.exists(self.automator.prev_backup) is False
                assert os.path.exists(self.automator.temp_backup)
            
