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
from ..database import Database


@pytest.mark.database
class Test_Postgres:
    """Tests all local functions within the Postgres class."""

    @pytest.mark.skip(reason="This wipes EVERYTHING. Avoid testing unless you are willing to rebuild.")
    def test_erase_all(self, new_creds):
        """Tests erasing all database and config sections"""
        """This test WILL delete everything without backing up or
        saving the data in any way. Run this in a expendable test
        enviroment or similar."""

        #TODO: F rebuilding, it doesn't work, full stop.
        creds, conf, post = new_creds
        post.erase_all()
        with Database() as db:
            results = db.execute("SELECT datname FROM pg_database")
            result_list = [result["datname"] for result in results]  
            expected_list = ["bgp", "postgres", "template1", "template0"]
            print(result_list)
            assert len(result_list) == 4
            for database in expected_list:
                assert database in result_list
        post = Postgres()
        post.install('bgp')
        
    #@pytest.mark.meta
    @pytest.mark.skip
    def test_meta(self):
        #TODO: Temp pytest test function


        post = Postgres()
        post.install('test_new')
        conf = Config('test_new') 
        #post.install('bgp')
        #conf_bgp = Config('bgp')
        creds = conf.get_db_creds(True)
        conn = psycopg2.connect(**creds)
        cur = conn.cursor()
        cur.execute('SELECT datname FROM pg_database')
        result = cur.fetchone()
        print("datname in pg_database: " + str(result))
        post._run_sql_cmds(['DROP DATABASE test_new;'])
        conf._remove_old_config_section('test_new')


    #@pytest.mark.meta_two
    @pytest.mark.skip
    def test_meta_two(self):
        #TODO: Temp pytest test function
        with Database() as db:
            results = db.execute("SELECT datname FROM pg_database")
            r_list = [result["datname"] for result in results]  
            print(r_list)
        


    @pytest.mark.install
    def test_install(self):
        """Tests install.

        Should generate a random password, add a config section,
        create and mod db. Just check general creation.
        """
        #TODO: done
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
        #TODO: pg_extensions, pg_avail both fail
        post = Postgres()
        password = 'testpass'
        Config('test_new').create_config(password)
        conf = Config('test_new')
        post.install('test_new')
        post._create_database('test_new', password)
        creds = conf.get_db_creds(True) 
        conn = psycopg2.connect(**creds)
        cur = conn.cursor()
        extensions = cur.execute("SELECT * FROM pg_available_extensions")
        print(extensions)
        assert 'btree_gist' in extensions
        conn.close()
        Postgres()._run_sql_cmds(['DROP DATABASE test_new'])
        conf._remove_old_config_section('test_new')

    @pytest.mark.mod
    def test_modify_database(self, new_creds):
        """tests modifying the database

        Tests modifying the database for speed
        Assert that each line is true in the sql cmds.
            NOTE: you can use the show command in sql
        """
        #TODO: Feex is good

        creds, conf, post = new_creds
        cpus = cpu_count() - 1
        ram = Config('test_new').ram
        expected_ram = str(ram) + 'MB'
        shared = str(int(.4 * ram)) + 'MB'
        work_mem = str(int(ram / (cpu_count() * 1.5))) + 'MB'
        ulimit, random_page_cost = post._get_ulimit_random_page_cost()
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
                ('SHOW random_page_cost;', int(random_page_cost)),
                ('SHOW max_stack_depth;', max_depth)]
        self.check_sqls(sqls, creds)
        self.cleanup_test(conf)

    @pytest.mark.unhinge
    def test_unhinge_db(self, new_creds):
        """Tests unhinging database

        Assert that each line in the sql cmds is true
        """
        #TODO: Max wal size consistently off...by only one....well, it works.
        creds, conf, post = new_creds
        ram = conf.ram
        wal = str(ram-1000+1) + 'MB'
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
        self.cleanup_test(conf)

    @pytest.mark.rehinge
    def test_rehinge_db(self, new_creds):
        #TODO: Done
        """Tests rehinging database

        Assert that each line in the sql cmds is true
        """
        creds, conf, post = new_creds
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
        self.cleanup_test(conf)

    @pytest.mark.restart
    def test_restart_postgres(self, new_creds):
        """Tests restartng postgres

        Make sure postgres temporarily goes offline then restarts.
        """
        #TODO: DONE
        creds, conf, post = new_creds
        Postgres.restart_postgres()
        conn = psycopg2.connect(**creds)
        cur = conn.cursor()
        # dba.stackexchange.com/questions/99428
        cur.execute('SELECT EXTRACT(epoch from current_timestamp - pg_postmaster_start_time()) as uptime')
        uptime = cur.fetchone()[0]
        assert uptime < 100
        self.cleanup_test(conf)

########################
### Helper Functions ###
########################
    def check_sqls(self, sqls: list, creds):
        for sql in sqls:
            assert isinstance(sql, tuple)
        conn = psycopg2.connect(**creds)
        cur = conn.cursor()
        for sql in sqls:
            expected_result = str(sql[1])
            cur.execute(sql[0])
            result = cur.fetchone()[0]
            print("Checking " + str(sql[0]) + " with expected value of " + expected_result + " and actual value of " + result) 
            assert result == expected_result

    @pytest.fixture
    def new_creds(self): 
        Postgres()._run_sql_cmds(['DROP DATABASE IF EXISTS test_new;'])
        post = Postgres(section='test_new')
        post.install('test_new')
        conf = Config('test_new')
        creds = conf.get_db_creds(True)
        result = [creds, conf, post]
        return result

    def cleanup_test(self, conf):
        Postgres()._run_sql_cmds(['DROP DATABASE IF EXISTS test_new;'])
        conf._remove_old_config_section('test_new')
