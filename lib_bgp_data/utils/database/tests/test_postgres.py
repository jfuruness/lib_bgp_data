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
import psycopg2
from multiprocessing import cpu_count
from ..postgres import Postgres
from ..config import Config


@pytest.mark.database
class Test_Postgres:
    """Tests all local functions within the Postgres class."""

    @pytest.mark.skip(reason="This wipes EVERYTHING. Avoid testing unless you are willing to rebuild.")
    def test_erase_all(self):
        """Tests erasing all database and config sections"""
        """This test WILL delete everything without backing up or
        saving the data in any way. Run this in a expendable test
        enviroment or similar."""
        
        post = Postgres()
        post.erase_all()
        result = post._run_sql_cmds(['SELECT datname FROM pg_database;'])
        assert result == None
        # Rebuild
        post.install('bgp')
        post.install('test')

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
        post._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new') 
        


    def test_create_database(self):
        """Tests the database creation

        Should create a new database with nothing in it
        Should create a new user
        Should have installed btree_gist extension
        """
        password = 'testpass' 
        Config('test_new').create_config(password)
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        conf._create_database('test_new', password)
        conn = psycopg2.connect(**creds)
        extensions = conn.execute("SELECT * FROM pg_extension")
        assert 'btree_gist' in extensions
        conn.close()
        Postgres()._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')
         
    @pytest.mark.temp
    def test_temp(self): 
        post = Postgres()
        post.install('test')

    def test_modify_database(self):
        """tests modifying the database

        Tests modifying the database for speed
        Assert that each line is true in the sql cmds.
            NOTE: you can use the show command in sql
        """
        password = 'testpass'
        Config('test_new').create_config(password)
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        conf._create_database('test_new', password)
        post = Postgres(section='test_new')
        
        cpus = cpu_count() - 1
        ram = conf.ram
        shared = str(int(.4 * ram)) + 'MB'
        work_mem = str(int(ram / cpu_count() * 1.5)) + 'MB'
        post._modify_database('test_new')
        sqls = [('SHOW timezone;', 'UTC'),
                ('SHOW fsync;', 'off'),
                ('SHOW synchronous_commit;', 'off'),
                ('SHOW full_page_writes;', 'off'),
                ('SHOW max_parallel_workers_per_gather;', cpus),
                ('SHOW max_parallel_workers;', cpus),
                ('SHOW max_worker_processes;', cpus*2),
                ('SHOW wal_level;', 'minimal'),
                ('SHOW archive_mode;', 'off'),
                ('SHOW max_wal_senders;', 0),
                ('SHOW shared_buffers;', shared),
                ('SHOW work_mem;', work_mem),
                ('SHOW effective_cache_size;', ram)]
        #todo: add ulimit, page cost
        self.check_sqls(sqls, *post)
        Postgres()._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.skip(reason="New hire work")
    def test_unhinge_db(self):
        """Tests unhinging database

        Assert that each line in the sql cmds is true
        """
        password = 'testpass' 
        Config('test_new').create_config(password)
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        conf._create_database('test_new', password)
        post = Postgres(section='test_new')
 
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
        self.check_sqls(sqls, *post)
        Postgres()._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.skip(reason="New hire work")
    def test_rehinge_db(self):
        """Tests rehinging database

        Assert that each line in the sql cmds is true
        """
        
        password = 'testpass' 
        Config('test_new').create_config(password)
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        conf._create_database('test_new', password)
        post = Postgres(section='test_new')

        sqls = [('SHOW checkpoint_timeout;', '5min'),
                ('SHOW checkpoint_completion_target;', .5),
                ('SHOW max_wal_size;', '1GB'),
                ('SHOW autovacuum;', 'ON'),
                ('SHOW autovacuum_max_workers;', 3),
                ('SHOW max_parallel_maintenance_workers;', 2),
                ('SHOW maintenance_work_mem;', '64MB')]
        self.check_sqls(sqls, *post)
        Postgres()._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')
       

    @pytest.mark.restart
    def test_restart_postgres(self):
        """Tests restartng postgres

        Make sure postgres temporarily goes offline then restarts.
        """ 
        post = Postgres()
        post.install('test_new')
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        conn = psycopg2.connect(**creds)
        Postgres.restart_postgres()
        # dba.stackexchange.com/questions/99428
        uptime = conn.execute('SELECT EXTRACT(epoch from current_timestamp - pg_postmaster_start_time()) as uptime')
        assert uptime < 100
        post._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')

######################
###Helper Functions###
######################
    @pytest.mark.sqlcheck
    def test_checker(self): 
        password = 'testpass' 
        Config('test_new').create_config(password)
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        conf._create_database('test_new', password)
        post = Postgres(section='test_new')
        sqls = ['SHOW maintenance_work_mem;', 'SHOW autovacuum_max_workers;', 'SHOW max_parallel_maintenance_workers;']
        for sql in sqls:
            print(connection._run_sql_cmds([sql]))

    def check_sqls(self, sqls: tuple, *connection):
        for sql in sqls:
            result = connection._run_sql_cmds([sql[0]])
            assert result == sql[1]
        
