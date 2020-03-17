#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class postgres

This class specifically deals with changing postgres configurations.
It contains functions to:
install database
unhinge database, making it really fast
restart postgres
erase all database configurations
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino", "Cameron Morris"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import logging
from multiprocessing import cpu_count
import os
import random
import string
import time

from configparser import ConfigParser as SCP
import pytest

from .config import Config
from ..utils import utils, config_logging


SQL_FILE_PATH = "/tmp/db_modify.sql"

class Postgres:
    """Configures database"""

    __slots__ = []

    sql_file_path = SQL_FILE_PATH

    def __init__(self, stream_level=logging.INFO, section=None):
        config_logging(stream_level, section)

    def erase_all(self):
        """Deletes config and all database sections"""

        # Check user inteded to erase everything
        _ans = input("You are about to erase the config file and drop all "
                     "Postgres databases. Enter 'Yes' to confirm.\n")
        if _ans.lower() != "yes":
            print("Did not drop databases")
            return
        # Use default path (get from Config?)
        path = Config.path
        # First delete the databases
        _conf = SCP()
        _conf.read(path)
        # Database names correspond to section headers
        # Exclude first since ConfigParser reserves for 'DEFAULT'
        _db_names = [x for x in _conf][1:]
        cmds = [f'sudo -u postgres psql -c "DROP DATABASE {db}"'
                for db in _db_names]
        utils.run_cmds(cmds)
        # Now remove the section from the config file
        # Fastest way to do this is create a new object
        # and write to the same location
        new_conf = SCP()
        with open(path, 'w+') as configfile:
            new_conf.write(configfile)

##############################
### Installation Functions ###
##############################

    def install(self, section: str):
        """Installs database and modifies it"""

        password = ''.join(random.SystemRandom().choice(
            string.ascii_letters + string.digits) for _ in range(24))

        Config(section).create_config(password)
        self._create_database(section, password)
        self._modify_database(section)

    # Must delete postgres history after setting password
    @utils.delete_files("/var/lib/postgresql.psql_history")
    def _create_database(self, section: str, password: str):
        """Creates database for specific section"""

        # SQL commands to write
        sqls = [f"DROP DATABASE {section};",
                f"DROP OWNED BY {section}_user;",
                f"DROP USER {section}_user;",
                f"CREATE DATABASE {section};",
                f"CREATE USER {section}_user;",
                f"REVOKE CONNECT ON DATABASE {section} FROM PUBLIC;",
                "REVOKE ALL ON ALL TABLES IN SCHEMA public"
                " FROM {section}_user;""",
                "GRANT ALL PRIVILEGES ON DATABASE "
                f"{section} TO {section}_user;",
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES "
                f"IN SCHEMA public TO {section}_user;",
                f"ALTER USER {section}_user WITH PASSWORD '{password}';",
                f"ALTER USER {section}_user WITH SUPERUSER;",
                "CREATE EXTENSION btree_gist WITH SCHEMA {section};"]

        self._run_sql_cmds(sqls)
        # Creates btree extension
        utils.run_cmds(f'sudo -u postgres psql -d {section}'
                       ' -c "CREATE EXTENSION btree_gist;"')

    def _modify_database(self, section: str):
        """Optimizes database for speed.

        The database will be corrputed if there is a crash. These changes
        work at a cluster level, so all the databases will be changed.
        """

        ram = Config(section).ram
        random_page_cost, ulimit = self._get_ulimit_random_page_cost()
        cpus = cpu_count() - 1
        sqls = ["CREATE EXTENSION btree_gist;",
                f"ALTER DATABASE {section} SET timezone TO 'UTC';",
                # These are settings that ensure data isn't corrupted in
                # the event of a crash. We don't care so...
                "ALTER SYSTEM SET fsync TO off;",
                "ALTER SYSTEM SET synchronous_commit TO off;",
                "ALTER SYSTEM SET full_page_writes TO off;",
                # Allows for parallelization
                f"ALTER SYSTEM SET max_parallel_workers_per_gather TO {cpus};",
                f"ALTER SYSTEM SET max_parallel_workers TO {cpus};",
                f"ALTER SYSTEM SET max_worker_processes TO {cpu_count() * 2};",

                # Writes as few logs as possible
                "ALTER SYSTEM SET wal_level TO minimal;",
                "ALTER SYSTEM SET archive_mode TO off;",
                "ALTER SYSTEM SET max_wal_senders TO 0;",
                # https://www.postgresql.org/docs/current/
                # runtime-config-resource.html
                # https://dba.stackexchange.com/a/18486
                # https://severalnines.com/blog/
                # setting-optimal-environment-postgresql
                # Buffers for postgres, set to 40%, and no more
                f"ALTER SYSTEM SET shared_buffers TO '{int(.4 * ram)}MB';",
                # Memory per process, since 11 paralell gathers and
                # some for vacuuming, set to ram/(1.5*cores)
                "ALTER SYSTEM SET work_mem TO "
                f"'{int(ram / (cpu_count() * 1.5))}MB';",
                # Total cache postgres has, ignore shared buffers
                f"ALTER SYSTEM SET effective_cache_size TO '{ram}MB';",
                # Set random page cost to 2 if no ssd, with ssd
                # seek time is one for ssds
                f"ALTER SYSTEM SET random_page_cost TO {random_page_cost};",
                # Yes I know I could call this, but this is just for machines
                # that might not have it or whatever
                # Gets the maximum safe depth of a servers execution stack
                # in kilobytes from ulimit -s
                # https://www.postgresql.org/docs/9.1/runtime-config-resource.html
                # Conversion from kb to mb then minus one
                "ALTER SYSTEM SET max_stack_depth TO "
                f"'{int(int(ulimit)/1000)-1}MB';"]

        self._run_sql_cmds(sqls)

##########################################
### Unhinging functions used for speed ###
##########################################

    def unhinge_db(self, *args, **kwargs):
        """Enhances database, but doesn't allow for writing to disk."""

        logging.info("unhinging db")
        from .config import global_section_header
        # access to section header
        ram = Config(global_section_header).ram
        # This will make it so that your database never writes to
        # disk unless you tell it to. It's faster, but harder to use
        sqls = [  # https://www.2ndquadrant.com/en/blog/
                # basics-of-tuning-checkpoints/
                # manually do all checkpoints to abuse this thing
                "ALTER SYSTEM SET checkpoint_timeout TO '1d';",
                "ALTER SYSTEM SET checkpoint_completion_target TO .9;",
                # The amount of ram that needs to be hit before a write do disk
                f"ALTER SYSTEM SET max_wal_size TO '{ram - 1000}MB';",
                # Disable autovaccum
                "ALTER SYSTEM SET autovacuum TO off;",
                # Change max number of workers
                # Since this is now manual it can be higher
                f"ALTER SYSTEM SET autovacuum_max_workers TO {cpu_count() - 1};",
                # Change the number of max_parallel_maintenance_workers
                # Since its manual it can be higher
                f"ALTER SYSTEM SET max_parallel_maintenance_workers TO {cpu_count() - 1};",
                f"ALTER SYSTEM SET maintenance_work_mem TO '{int(ram / 5)}MB';"]
        self._run_sql_cmds(sqls)
        self.restart_postgres()
        logging.debug("unhinged db")

    @staticmethod
    def rehinge_db(self):
        """Restores postgres 11 defaults"""


        logging.info("rehinging db")
        # This will make it so that your database never writes to
        # disk unless you tell it to. It's faster, but harder to use
        sqls = [  # https://www.2ndquadrant.com/en/blog/
                # basics-of-tuning-checkpoints/
                # manually do all checkpoints to abuse this thing
                "ALTER SYSTEM SET checkpoint_timeout TO '5min';",
                "ALTER SYSTEM SET checkpoint_completion_target TO .5;",
                # The amount of ram that needs to be hit before a write do disk
                "ALTER SYSTEM SET max_wal_size TO '1GB';",
                # Disable autovaccum
                "ALTER SYSTEM SET autovacuum TO ON;",
                # Change max number of workers
                # Since this is now manual it can be higher
                "ALTER SYSTEM SET autovacuum_max_workers TO 3;",
                # Change the number of max_parallel_maintenance_workers
                # Since its manual it can be higher
                "ALTER SYSTEM SET max_parallel_maintenance_workers TO 2;",
                "ALTER SYSTEM SET maintenance_work_mem TO '64MB';"]
        self._run_sql_cmds(sqls) 
        self.restart_postgres()
        logging.debug("rehinged db")

    @staticmethod
    def restart_postgres():
        """Restarts postgres and all connections."""

        logging.debug("About to restart postgres")
        if hasattr(self, "close"):
            self.close()
        # access to section header
        utils.run_cmds(Config(global_section_header).restart_postgres_cmd)
        time.sleep(30)
        logging.debug("Restarted postgres")
        if hasattr(self, "_connect"):
            self._connect()

########################
### Helper Functions ###
########################

    @utils.delete_files(SQL_FILE_PATH)
    def _run_sql_cmds(self, sqls: list):
        """Writes the sql file that is later run"""

        # Writes sql file
        with open(self.sql_file_path, "w+") as _db_mod_file:
            for sql in sqls:
                assert ";" in sql, f"{sql} statement has no ;"
                _db_mod_file.write(sql + "\n")
        # Runst he sql commands
        utils.run_cmds(f"sudo -u postgres psql -f {Postgres.sql_file_path}")

    def _get_ulimit_random_page_cost(self) -> tuple:
        """Gets ulimit and random page cost"""

        if hasattr(pytest, 'global_running_test') \
           and pytest.global_running_test:
                random_page_cost = float(1)
                ulimit = 8192
        # Otherwise get from user
        else:
            usr_input = input("If SSD, enter 1 or enter, else enter 2: ")
            if str(usr_input) in ["", "1"]:
                random_page_cost = float(1)
            else:
                random_page_cost = float(2)
            ulimit = input("Enter the output of ulimit -s or press enter for 8192: ")
            if ulimit == "":
                ulimit = 8192
            else:
                ulimit = int(ulimit)

        return ulimit, random_page_cost
