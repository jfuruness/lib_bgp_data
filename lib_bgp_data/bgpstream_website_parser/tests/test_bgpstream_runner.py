#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = "Tony Zheng"
__credits__ = "Tony Zheng"
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
import subprocess

import pytest
import shutil

from ..bgpstream_runner import BGPStream_Website_Runner
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..tables import Hijacks_Table, Leaks_Table, Outages_Table


# has to be here because parametrization collects before class is created
def table_list():
    return [Hijacks_Table, Leaks_Table, Outages_Table]

class Test_BGPStream_Website_Runner:

    # use a different dir as to not overwrite backups
    test_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'backups')

    @pytest.fixture()
    def runner(self, scope='class'):
        """Scoped to class so BGPStream_Website_Parser only needs to run once.
        Creates test directory as to not overwrite real backups."""

        BGPStream_Website_Parser()._run(row_limit=35)
        runner = BGPStream_Website_Runner()
        runner.backup_dir = self.test_dir
        yield runner
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @pytest.mark.slow()
    def test_run(self, runner):
        """Make backups and delete tables to test runner's ability to detect
        missing tables."""

        for table in table_list():
            runner.backup(table)

            with table() as db:
                db.execute(f'DROP TABLE IF EXISTS {table.name}')

        runner._run()            
        
    @pytest.mark.parametrize('table', table_list())
    def test_backup(self, runner, table):
        """Check backup files are created and temp is deleted"""

        runner.backup(table)
        assert os.path.exists(os.path.join(runner.backup_dir,
                                        f'{table.name}.sql.gz'))
        assert not os.path.exists(os.path.join(runner.backup_dir,
                                              'temp.sql.gz'))

    @pytest.mark.parametrize('table', table_list())
    def test_restore(self, runner, table):
        """Trying to restore backups that don't exist should error"""

        with pytest.raises(subprocess.CalledProcessError):
            runner.restore('nonexistant', table())

        runner.backup(table)
        runner.restore(os.path.join(self.test_dir, f'{table.name}.sql.gz'), table())

    def test_pg_cmd(self, runner):
        """Run a command that would fail if user is not postgres"""
        runner.pg_cmd('psql bgp -l')


