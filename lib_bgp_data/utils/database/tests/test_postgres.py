#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the postgres.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest
import time
import psycopg2
from multiprocessing import cpu_count
from ..postgres import Postgres
from ..config import Config


@pytest.mark.database
class Test_Postgres:
    """Tests all local functions within the Postgres class."""

    @pytest.mark.skip(reason="This wipes EVERYTHING. Avoid testing unless you are willing to rebuild.")
    #TODO: This test fails for some goddamn reason.
    def test_erase_all(self):
        """Tests erasing all database and config sections"""
        """This test WILL delete everything without backing up or
        saving the data in any way. Run this in a expendable test
        enviroment or similar."""
        post = Postgres()
        post.install('bgp')
        post.install('test')
        post.erase_all()
        result = post._run_sql_cmds(['SELECT datname FROM pg_database;'])
        assert result is None
        # Rebuild
        post.install('bgp')
        post.install('test')

    @pytest.mark.meta
    #@pytest.mark.skip
    def test_meta(self):
        #TODO: Temp pytest test function
        print('foo')

        post = Postgres()
        post.install('bgp')
        post.install('test')

    @pytest.mark.install
    def test_install(self):
        """Tests install.

        Should generate a random password, add a config section,
        create and mod db. Just check general creation.
        """
        post = Postgres()
        post.install('test_new')
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        # Checking
        conn = psycopg2.connect(**creds)
        conn.close()
        post._run_sql_cmds(['DROP DATABASE test_new;'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.create
    def test_create_database(self):
        """Tests the database creation

        Should create a new database with nothing in it
        Should create a new user
        Should have installed btree_gist extension
        """
        post = Postgres()
        password = 'testpass'
        Config('test_new').create_config(password)
        conf = Config('test_new')
        post.install('test_new')
        post._create_database('test_new', password)
        creds = conf.get_db_creds(True) 
        conn = psycopg2.connect(**creds) 
        cur = conn.cursor()
        extensions = cur.execute("SELECT * FROM pg_extension")
        assert 'btree_gist' in extensions
        conn.close()
        Postgres()._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.mod
    def test_modify_database(self):
        """tests modifying the database

        Tests modifying the database for speed
        Assert that each line is true in the sql cmds.
            NOTE: you can use the show command in sql
        """

        Postgres()._run_sql_cmds(['DROP DATABASE IF EXISTS test_new;'])
        post = Postgres(section='test_new')
        post.install('test_new')
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        cpus = cpu_count() - 1
        ram = Config('test_new').ram
        expected_ram = str(ram) + 'MB'
        shared = str(int(.4 * ram)) + 'MB'
        work_mem = str(int(ram / (cpu_count() * 1.5))) + 'MB'
        random_page_cost, ulimit = post._get_ulimit_random_page_cost()
        max_depth = str(int(int(ulimit)/1000)-1) + 'MB'
        post._modify_database('test_new')
        sqls = [('SHOW timezone;', 'UTC'),
                ('SHOW fsync;', 'off'),
                ('SHOW synchronous_commit;', 'off'),
                ('SHOW full_page_writes;', 'off'),
                ('SHOW max_parallel_workers_per_gather;', cpus),
                ('SHOW max_parallel_workers;', cpus),
                ('SHOW max_worker_processes;', cpu_count()*2),
                ('SHOW wal_level;', 'minimal'),
                ('SHOW archive_mode;', 'off'),
                ('SHOW max_wal_senders;', 0),
                ('SHOW shared_buffers;', shared),
                ('SHOW work_mem;', work_mem),
                ('SHOW effective_cache_size;', expected_ram),
                # RAM changes mid-test....so setting this aside for now
                ('SHOW random_page_cost;', random_page_cost),
                ('SHOW max_stack_depth;', max_depth)]
        self.check_sqls(sqls, creds)
        Postgres()._run_sql_cmds(['DROP DATABASE test_new;'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.unhinge
    def test_unhinge_db(self):
        """Tests unhinging database

        Assert that each line in the sql cmds is true
        """

        Postgres()._run_sql_cmds(['DROP DATABASE IF EXISTS test_new;'])
        post = Postgres(section='test_new')
        post.install('test_new')
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        ram = conf.ram
        wal = str(ram-1000) + 'MB'
        maint_mem = str(int(ram / 5)) + 'MB'
        post.unhinge_db()
        sqls = [('SHOW checkpoint_timeout;', '1d'),
                ('SHOW checkpoint_completion_target;', .9),
                ('SHOW max_wal_size;', wal),
                ('SHOW autovacuum;', 'off'),
                ('SHOW autovacuum_max_workers;', cpu_count() - 1),
                ('SHOW max_parallel_maintenance_workers;', cpu_count() - 1),
                ('SHOW maintenance_work_mem;', maint_mem)]
        Postgres().restart_postgres()
        self.check_sqls(sqls, creds)
        Postgres()._run_sql_cmds(['DROP DATABASE test_new;'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.rehinge
    def test_rehinge_db(self):
        """Tests rehinging database

        Assert that each line in the sql cmds is true
        """
        Postgres()._run_sql_cmds(['DROP DATABASE IF EXISTS test_new;'])
        post = Postgres(section='test_new')
        post.install('test_new')
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        post.rehinge_db(post)
        sqls = [('SHOW checkpoint_timeout;', '5min'),
                ('SHOW checkpoint_completion_target;', .5),
                ('SHOW max_wal_size;', '1GB'),
                ('SHOW autovacuum;', 'on'),
                ('SHOW autovacuum_max_workers;', 3),
                ('SHOW max_parallel_maintenance_workers;', 2),
                ('SHOW maintenance_work_mem;', '64MB')]
        Postgres().restart_postgres()
        self.check_sqls(sqls, creds)
        Postgres()._run_sql_cmds(['DROP DATABASE test_new;'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.restart
    def test_restart_postgres(self):
        """Tests restartng postgres

        Make sure postgres temporarily goes offline then restarts.
        """
        #TODO: DONE
        post = Postgres()
        post.install('test_new')
        conf = Config('test_new') 
        Postgres.restart_postgres()
        creds = conf.get_db_creds(True)
        conn = psycopg2.connect(**creds)
        cur = conn.cursor()
        # dba.stackexchange.com/questions/99428
        cur.execute('SELECT EXTRACT(epoch from current_timestamp - pg_postmaster_start_time()) as uptime')
        uptime = cur.fetchone()[0]
        assert uptime < 100
        post._run_sql_cmds(['DROP DATABASE test_new;'])
        conf._remove_old_config_section('test_new')

########################
### Helper Functions ###
########################
    def check_sqls(self, sqls: tuple, creds):
        conn = psycopg2.connect(**creds)
        cur = conn.cursor()
        for sql in sqls:
            expected_result = str(sql[1])
            cur.execute(sql[0])
            result = cur.fetchone()[0]
            print("Checking " + str(sql[0]) + " with expected value of " + expected_result + " and actual value of " + result) 
            assert result == expected_result
