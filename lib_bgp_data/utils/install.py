#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Install.

The Install class contains the functionality to create through a script
everything that is needed to be used for the program to run properly.
This is done through a series of steps.

1. Create the config file. This is optional in case a config was created
    -This is handled by the config class
    -The fresh_install arg is by default set to true for a new config
2. Install the new database and database users. This is optional.
    -This is handled by _create_database
    -If a new config is created, a new database will be created
3. Then the database is modified.
    -This is handled by modify_database
    -If unhinged argument is passed postgres won't write to disk
        -All writing to disk must be forced with vaccuum
        -If data isn't written to disk then memory will be leaked
4. Then the extrapolator is installed
    -Handled in the _install_extrapolator and
     _install_rovpp_extrapolator function
    -The rov and forecast versions of the extrapolator are isntalled
    -The extrapolators are copied into /usr/bin for later use
5. Then bgpscanner is installed
    -Handled in the _install_bgpscanner function
    -Once it is isntalled it is copied into /usr/bin for later use
6. Then bgpdump is installed
    -Handled in the _install_bpdump function
    -Must be installed from source due to bug fixes
    -Copied to /usr/bin for later use
7. Then the rpki validator is installed
    -Handled in the _install_rpki_validator functions
    -Config files are swapped out for our own
    -Installed in /var/lib

Design choices (summarizing from above):
    -Database modifications increase speed
        -Tradeoff is that upon crash corruption occurs
        -These changes are made at a cluster level
            -(Some changes affect all databases)
    -bgpdump must be installed from source due to bug fixes

Possible Future Extensions:
    -Add test cases
    -Move install scripts to different files, or SQL files, or to their
     respective submodules
    -I shouldn't have to change lines in the extrapolator to get it to run
"""

import functools
import random
import string
import pytest
from getpass import getpass
from subprocess import check_call, call
import os
from multiprocess import cpu_count
import fileinput
import sys
from .config import Config
from .utils import delete_paths, delete_files

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino", "Cameron Morris"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# Global is used for decorator
sql_install_file = "/tmp/db_install.sql"


class Install:
    """Installs and configures the lib_bgp_data package"""

    __slots__ = ['section', 'logger', 'db_pass']

    
    def __init__(self, section="bgp"):
        """Makes sure that you are a sudo user"""

        class NotSudo(Exception):
            pass

        DEBUG = 10  # Cannot import logging due to deadlocks
        # Initializes self.logger
        self.logger = Logger(stream_level=DEBUG)
        # Store the section header for the config file
        self.section = section
        # Makes sure that you are a sudo user
        if os.getuid() != 0:
            raise NotSudo("Sudo priveleges are required for install")

    
    def install(self, fresh_install=True, password=False):
        """Installs everything"""

        if fresh_install:
            # Gets password for database
            if password:
                self.db_pass = getpass("Password for database: ")
            else:
                password_characters = string.ascii_letters + string.digits
                self.db_pass = ''.join(random.SystemRandom().choice(
                    password_characters) for i in range(24))
            Config(self.logger, self.section).create_config(self.db_pass)
            self._create_database()
        # Set unhinged to true to prevent automated writes to disk
        self._modify_database()
        self._install_forecast_extrapolator()
        self._install_rovpp_extrapolator()
        self._install_bgpscanner()
        self._install_bgpdump()
        self._install_rpki_validator()
        # Install a 'test' section
        # Use this check to prevent looping calls
        if self.section != "test":
            Install("test").install()

    # Must remove that file due to password change history
    
    @delete_files([sql_install_file, "/var/lib/postgresql/.psql_history"])
    def _create_database(self):
        """Creates the bgp database and bgp_user and extensions."""

        # SQL commands to write
        sqls = ["DROP DATABASE {};".format(self.section),
                "DROP OWNED BY {}_user;".format(self.section),
                "DROP USER {}_user;".format(self.section),
                "CREATE DATABASE {};".format(self.section),
                "CREATE USER {}_user;".format(self.section),
                "REVOKE CONNECT ON DATABASE "
                "{} FROM PUBLIC;".format(self.section),
                "REVOKE ALL ON ALL TABLES IN SCHEMA "
                "public FROM {}_user;".format(self.section),
                "GRANT ALL PRIVILEGES ON DATABASE "
                "{} TO {}_user;".format(self.section, self.section),
                """GRANT ALL PRIVILEGES ON ALL SEQUENCES
                IN SCHEMA public TO {}_user;""".format(self.section),
                "ALTER USER {}_user WITH PASSWORD '{}';".format(self.section,
                                                                self.db_pass),
                "ALTER USER {}_user WITH SUPERUSER;".format(self.section),
                "CREATE EXTENSION btree_gist "
                "WITH SCHEMA {};".format(self.section)]
        # Writes sql file
        self._run_sql_file(sqls)
        # Must do this here, nothing else seems to create it
        create_extension_args = ('sudo -u postgres psql -d {}'
                                 ' -c "CREATE EXTENSION '
                                 'btree_gist;"'.format(self.section))
        # Allow for failures in case it's already there
        call(create_extension_args, shell=True)

    
    @delete_files(sql_install_file)
    def _modify_database(self):
        """Modifies the database for speed.

        Makes it so that the database is optimized for speed. The
        database will be corrupted if there is a crash. These changes
        work at a cluster level, so all databases will be changed.
        """

        ram = Config(self.logger, self.section).ram
        # Can't take input during tests
        # Error when Pytest is not running
        if hasattr(pytest, 'global_running_install_test') \
           and pytest.global_running_install_test:
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
        # Extension neccessary for some postgres scripts
        sqls = ["CREATE EXTENSION btree_gist;",
                "ALTER DATABASE {} SET timezone "
                "TO 'UTC';".format(self.section),
                # These are settings that ensure data isn't corrupted in
                # the event of a crash. We don't care so...
                "ALTER SYSTEM SET fsync TO off;",
                "ALTER SYSTEM SET synchronous_commit TO off;",
                "ALTER SYSTEM SET full_page_writes TO off;",
                # Allows for parallelization
                """ALTER SYSTEM SET max_parallel_workers_per_gather
                TO {};""".format(cpu_count() - 1),
                "ALTER SYSTEM SET max_parallel_workers TO {};".format(
                    cpu_count() - 1),
                "ALTER SYSTEM SET max_worker_processes TO {};".format(
                    cpu_count() * 2),

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
                "ALTER SYSTEM SET shared_buffers TO '{}MB';".format(
                    int(.4 * ram)),
                # Memory per process, since 11 paralell gathers and
                # some for vacuuming, set to ram/(1.5*cores)
                "ALTER SYSTEM SET work_mem TO '{}MB';".format(
                    int(ram / (cpu_count() * 1.5))),
                # Total cache postgres has, ignore shared buffers
                "ALTER SYSTEM SET effective_cache_size TO '{}MB';".format(ram),
                # Set random page cost to 2 if no ssd, with ssd
                # seek time is one for ssds
                "ALTER SYSTEM SET random_page_cost TO {};".format(
                    random_page_cost),
                # Yes I know I could call this, but this is just for machines
                # that might not have it or whatever
                # Gets the maximum safe depth of a servers execution stack
                # in kilobytes from ulimit -s
                # https://www.postgresql.org/docs/9.1/runtime-config-resource.html
                # Conversion from kb to mb then minus one
                "ALTER SYSTEM SET max_stack_depth TO '{}MB';".format(
                    int(int(ulimit)/1000)-1)]

        self._run_sql_file(sqls)

    
    @delete_files("BGPExtrapolator/")
    def _install_forecast_extrapolator(self):
        """Installs forecast-extrapolator.

        Moved to to /usr/bin/forecast-extrapolator.
        """

        # Commands to install original extrapolator
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator/Misc",
                "sudo ./apt-install-deps.sh",
                "sudo apt -y install libboost-test-dev",
                "cd ..",
                "make -j{}".format(cpu_count()),
                "sudo cp bgp-extrapolator /usr/bin/forecast-extrapolator",
                "sudo cp bgp-extrapolator /usr/local/bin/forecast-extrapolator"]
        check_call("&& ".join(cmds), shell=True)

    
    @delete_files("BGPExtrapolator/")
    def _install_rovpp_extrapolator(self):
        """Installs rovpp-extrapolator.

        Moved to to /usr/bin/rovpp-extrapolator.
        """

        # Commands to install rovpp extrapolator
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator/Misc",
                "sudo ./apt-install-deps.sh",
                "sudo apt -y install libboost-test-dev",
                "cd ..",
                "git checkout remotes/origin/rovpp2",
                "git checkout -b rovpp2"]

        check_call("&& ".join(cmds), shell=True)

        # Change location of the conf file
        path = "BGPExtrapolator/SQLQuerier.cpp"
        prepend = '    string file_location = "'
        replace = './bgp.conf";'
        replace_with = '/etc/bgp/bgp.conf";'

        self._replace_line(path, prepend, replace, replace_with)

        # Install extrapolator
        cmds = ["cd BGPExtrapolator",
                "make -j{}".format(cpu_count()),
                "sudo cp bgp-extrapolator /usr/bin/rovpp-extrapolator",
                "sudo cp bgp-extrapolator /usr/local/bin/rovpp-extrapolator"]

        check_call("&& ".join(cmds), shell=True)

    
    def _erase_all(self):
        """Deletes config section and drops database from Postgres"""

        # Check user inteded to erase everything
        ans = input("You are about to erase the config file and drop all "
                        "Postgres databases.  Enter 'Yes' to confirm.\n")
        if ans.lower() != "yes":
            return
        # Use default path (get from Config?)
        path = "/etc/bgp/bgp.conf"
        # First delete the databases
        _conf = SCP()
        _conf.read(path)
        # Database names correspond to section headers
        # Exclude first since ConfigParser reserves for 'DEFAULT'
        db_names = [x for x in _conf][1:]
        cmds = ['sudo -u postgres psql -c "DROP DATABASE {}"'.format(db)
                for db in db_names]
        check_call("&& ".join(cmds), shell=True)
        # Now remove the section from the config file
        # Fastest way to do this is create a new object
        # and write to the same location
        new_conf = SCP()
        with open(self.path, 'w+') as configfile:
            new_conf.write(configfile)

########################
### Helper Functions ###
########################

    
    @delete_files(sql_install_file)
    def _run_sql_file(self, sqls):
        """Writes sql file"""

        with open(sql_install_file, "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        bash = "sudo -u postgres psql -f {}".format(sql_install_file)
        check_call(bash, shell=True)

    
    def _replace_line(self, path, prepend, line_to_replace, replace_with):
        """Replaces a line withing a file that has the path path"""

        lines = [prepend + x for x in [line_to_replace, replace_with]]
        for line in fileinput.input(path, inplace=1):
            line = line.replace(*lines)
            sys.stdout.write(line)
