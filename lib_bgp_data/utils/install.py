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
    -Handled in the _install_extrapolator function
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
    -Documentation coming later ############

Design choices (summarizing from above):
    -Database modifications increase speed
        -Tradeoff is that upon crash corruption occurs
        -These changes are made at a cluster level
            -(Some changes affect all databases)
    -The database can be unhinged so that it never writes do disk
        -This would allow most processing to be done in RAM
        -Writes to disk must be manually called
    -bgpdump must be installed from source due to bug fixes

Possible Future Extensions:
    -Add rpki validator installation and documentation
    -Automate the changing of bgpscanner to not ignore announcements
    -For the rovpp extrapolator, a line has to be changed in the source
    -Add test cases
"""

from getpass import getpass
from subprocess import call, check_call
import os
from multiprocess import cpu_count
from logging import DEBUG
import fileinput
import sys
from shutil import rmtree
from .logger import Thread_Safe_Logger as logger, error_catcher
from .config import Config

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Install:
    """Installs and configures the lib_bgp_data package"""

    __slots__ = ['logger', 'db_pass']

    @error_catcher()
    def __init__(self):
        """Makes sure that you are a sudo user"""

        class NotSudo(Exception):
            pass

        # Initializes self.logger
        self.logger = logger({"stream_level": DEBUG})
        # Makes sure that you are a sudo user
        if os.getuid() != 0:
            raise NotSudo("Sudo priveleges are required for install")

    @error_catcher()
    def install(self, fresh_install=True, unhinged=False):
        """Installs everything"""

        if fresh_install:
            # Gets password for database
            self.db_pass = getpass("Password for database: ")
            Config(self.logger).create_config(self.db_pass)
            self._create_database()
        # Set unhinged to true to prevent automated writes to disk
        self._modify_database(unhinged)
        self._install_extrapolator()
        self._install_bgpscanner()
        self._install_bgpdump()
        self._install_rpki_validator()

    @error_catcher()
    def _create_database(self):
        """Creates the bgp database and bgp_user"""

        # SQL commands to write
        sqls = ["DROP DATABASE bgp;",
                "DROP USER bgp_user;",
                "CREATE DATABASE bgp;",
                "CREATE USER bgp_user;",
                "REVOKE CONNECT ON DATABASE bgp FROM PUBLIC;"
                "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM bgp_user;",
                "GRANT ALL PRIVILEGES ON DATABASE bgp TO bgp_user;",
                """GRANT ALL PRIVILEGES ON ALL SEQUENCES
                IN SCHEMA public TO bgp_user;""",
                "ALTER USER bgp_user WITH PASSWORD '{}';".format(self.db_pass),
                "ALTER USER bgp_user WITH SUPERUSER;"]
        # Writes sql file
        with open("/tmp/db_install.sql", "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_install.sql", shell=True)
        # Removes sql file
        self._remove("/tmp/db_install.sql")
        # Removes postgres history to delete password change
        self._remove("/var/lib/postgresql/.psql_history")

    @error_catcher()
    def _modify_database(self, unhinge=False):
        """Modifies the database for speed.

        Makes it so that the database is optimized for speed. The
        database will be corrupted if there is a crash. These changes
        work at a cluster level, so all databases will be changed"""

        # First get the amount of ram 
        print("The amount of ram can be found with free -h, shown below")
        check_call("free -h", shell=True)
        ram = int(input("What is the amount of ram on the system in MB? "))
        # Extension neccessary for some postgres scripts
        sqls = ["CREATE EXTENSION IF NOT EXISTS btree_gist;",
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
                    float(input("If SSD, enter 1, else enter 2: ")))]
        if unhinge:
            # This will make it so that your database never writes to
            # disk unless you tell it to. It's faster, but harder to use
            sqls.extend([
                # https://www.2ndquadrant.com/en/blog/
                # basics-of-tuning-checkpoints/
                # manually do all checkpoints to abuse this thing
                "ALTER SYSTEM SET checkpoint_timeout TO '1d';",
                "ALTER SYSTEM SET checkpoint_completion_target TO .9;",
                # The amount of ram that needs to be hit before a write do disk
                "ALTER SYSTEM SET max_wal_size TO '{}MB';".format(ram-1000),
                # Disable autovaccum
                "ALTER SYSTEM SET autovacuum TO off;",
                # Change max number of workers
                # Since this is now manual it can be higher
                "ALTER SYSTEM SET autovacuum_max_workers TO {};".format(
                    cpu_count() - 1),
                # Change the number of max_parallel_maintenance_workers 
                # Since its manual it can be higher
                "ALTER SYSTEM SET max_parallel_maintenance_workers TO {};"\
                    .format(cpu_count() - 1),
                "ALTER SYSTEM maintenance_work_mem TO '{}MB';".format(
                    int(ram/5))])
                # Couldn't figure out this part exactly so it's commented out
                # Yes I know I could call this, but this is just for machines
                # that might not have it or whatever
                # stack_limit = int(input("What is the output of ulimit -s?"))
                # https://www.postgresql.org/docs/9.1/runtime-config-resource.html 
                #"ALTER SYSTEM SET max_stack_depth TO '{}MB';".format(
                # int(stack_limit/1024)-1)]

        # Writes sql file
        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        # Removes sql file to clean up
        self._remove("/tmp/db_modify.sql")

    @error_catcher()
    def _install_extrapolator(self):
        """Installs both versions of the extrapolator

        Moves to /usr/bin/rovpp-extrapolator
        Moves to /usr/bin/forecast-extrapolator"""

        # Warning just in case extrapolator is in development
        input("About to delete BGPExtrapolator if exists, press any key")
        # Removes extrapolator
        self._remove("BGPExtrapolator/")
        # Commands to install original extrapolator
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator/Misc",
                "sudo ./apt-install-deps.sh",
                "sudo apt install libboost-test-dev",
                "cd ..",
                "make -j{}".format(cpu_count()),
                "cp bgp-extrapolator /usr/bin/forecast-extrapolator",
                "rm -rf BGPExtrapolator"]
        check_call("&& ".join(cmds), shell=True)

        # Commands to install rovpp extrapolator
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator",
                "git checkout remotes/origin/rovpp",
                "git checkout -b rovpp"]

        # Must change this line - should be changed in extrapolator
        for line in fileinput.input("BGPExtrapolator/SQLQuerier.cpp",
                                    inplace=1):
            line = line.replace('    string file_location = "./bgp.conf";',
                                '    string file_location = "/etc/bgp/bgp.conf";')
            sys.stdout.write(line)

        # Install extrapolator
        cmds = ["cd BGPExtrapolator",
                "make -j{}".format(cpu_count()),
                "cp bgp-extrapolator /usr/bin/rovpp-extrapolator"]

        check_call("&& ".join(cmds), shell=True)
        # Remove unnessecary stuff
        self._remove("BGPExtrapolator/")

    def _install_rpki_validator(self):
        pass

    def _install_bgpscanner(self):
        """Installs bgpscanner and moves to /usr/bin/bgpscanner"""

        self._remove("bgpscanner/")

        cmds = ["sudo apt install meson",
                "sudo apt install zlib1g",
                "sudo apt install zlib1g-dev",
                "sudo apt-get install libbz2-dev",
                "sudo apt-get install liblzma-dev",
                "sudo apt-get install liblz4-dev",
                "git clone https://gitlab.com/Isolario/bgpscanner.git",
                "cd bgpscanner",
                "mkdir build && cd build",
                "meson ..",
                "ninja",
                "cp bgpscanner /usr/bin/bgpscanner"]
        check_call("&& ".join(cmds), shell=True)
        self._remove("bgpscanner")

    def _install_bgpdump(self):
        """Installs bgpdump and moves it to /usr/bin/bgpdump.

        Must be installed from source due to bug fixes not in apt repo.
        """

        # Removes old bgpdump stuff
        self._remove("bgpdump/")

        # Commands to install from source
        cmds = ["sudo apt install mercurial",
                "hg clone https://bitbucket.org/ripencc/bgpdump",
                "cd bgpdump",
                "sudo apt install automake",
                "./bootstrap.sh",
                "make",
                "./bgpdump -T",
                "cp bgpdump /usr/bin/bgpdump"]
        check_call("&& ".join(cmds), shell=True)
        # Removes bgpdump unnessecary stuff
        self._remove("bgpdump/")

    def _remove(self, remove_me):
        """Tries to remove a file or directory."""
        try:
            # If the path exists and is a file:
            if os.path.exists(remove_me) and os.path.isfile(remove_me):
                # Remove the file
                os.remove(remove_me)
            else:
                # It's a directory and remove that
                rmtree(remove_me)
        except FileNotFoundError:
            # If the file is not found nbd
            # This is just to clean out for a fresh install
            self.logger.debug("{} was not previously installed".format(remove_me))
