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

import random
import string
from getpass import getpass
from subprocess import check_call, call
import os
from multiprocess import cpu_count
# From logging module, but can't import it because it deadlocks!!!!!
DEBUG = 10
import fileinput
import sys
from shutil import rmtree
from .logger import Thread_Safe_Logger as logger, error_catcher
from .config import Config
from .database import Database, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
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
    def install(self, fresh_install=True, unhinged=False, password=False):
        """Installs everything"""

        if fresh_install:
            # Gets password for database
            if password:
                self.db_pass = getpass("Password for database: ")
            else:
                password_characters = string.ascii_letters + string.digits
                self.db_pass = ''.join(random.SystemRandom().choice(password_characters) for i in range(24))
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
                "ALTER USER bgp_user WITH SUPERUSER;",
                "CREATE EXTENSION btree_gist WITH SCHEMA bgp;"]
        # Writes sql file
        with open("/tmp/db_install.sql", "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_install.sql", shell=True)
        create_extension_args = ('sudo -u postgres psql -d bgp'
                                 ' -c "CREATE EXTENSION btree_gist;"')
        call(create_extension_args, shell=True)
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

        ram = Config(self.logger).ram
        # Extension neccessary for some postgres scripts
        sqls = ["CREATE EXTENSION btree_gist;",
                "ALTER DATABASE bgp SET timezone TO 'UTC';",
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
                    float(input("If SSD, enter 1, else enter 2: "))),
                # Yes I know I could call this, but this is just for machines
                # that might not have it or whatever
                # Gets the maximum safe depth of a servers execution stack in kilobytes from ulimit -s
                # https://www.postgresql.org/docs/9.1/runtime-config-resource.html
                "ALTER SYSTEM SET max_stack_depth TO '{}MB';".format(
                int(int(input("What is the output of ulimit -s?"))/1000)-1)]  # Conversion from kb to mb then minus one

        self._remove("/tmp/db_install.sql")
        with open("/tmp/db_install.sql", "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        # Calls sql file
        check_call("sudo -u postgres psql -f /tmp/db_install.sql", shell=True)
        # Removes sql file
        self._remove("/tmp/db_install.sql")

        # This will make the restart happen here
        with db_connection(Database, self.logger) as db:
            if unhinge:
                # This will make it so that your database never writes to
                # disk unless you tell it to. It's faster, but harder to use
                db.unhinge_db()
            else:
                db.rehinge_db()
        

    @error_catcher()
    def _install_extrapolator(self):
        """Installs both versions of the extrapolator

        Moves to /usr/bin/rovpp-extrapolator
        Moves to /usr/bin/forecast-extrapolator"""

        # Removes extrapolator
        self._remove("BGPExtrapolator/")
        # Commands to install original extrapolator
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator/Misc",
                "sudo ./apt-install-deps.sh",
                "sudo apt install libboost-test-dev",
                "cd ..",
                "make -j{}".format(cpu_count()),
                "sudo cp bgp-extrapolator /usr/bin/forecast-extrapolator",
                "rm -rf BGPExtrapolator"]
        check_call("&& ".join(cmds), shell=True)

        # Commands to install rovpp extrapolator
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator",
                "git checkout remotes/origin/rovpp",
               "git checkout -b rovpp"]

        path = "BGPExtrapolator/SQLQuerier.cpp"
        prepend = '    string file_location = "'
        replace = './bgp.conf";'
        replace_with = '/etc/bgp/bgp.conf";'

        self._replace_line(path, prepend, replace, replace_with)

        # Install extrapolator
        cmds = ["cd BGPExtrapolator",
                "make -j{}".format(cpu_count()),
                "sudo cp bgp-extrapolator /usr/bin/rovpp-extrapolator"]

        check_call("&& ".join(cmds), shell=True)
        # Remove unnessecary stuff
        self._remove("BGPExtrapolator/")

    def _install_rpki_validator(self):
        self._remove("rpki-validator/")

        rpki_url = ("https://ftp.ripe.net/tools/rpki/validator3/beta/generic/"
                    "rpki-validator-3-latest-dist.tar.gz")
        arin_tal = ("https://www.arin.net/resources/manage/rpki/"
                    "arin-ripevalidator.tal")
        # This is the java version they use so we will use it
        cmds = ["sudo apt-get install openjdk-8-jre",
                "wget {}".format(rpki_url),
                "tar -xvf rpki-validator-3-latest-dist.tar.gz",
                "rm -rf rpki-validator-3-latest-dist.tar.gz",
                "mv rpki-validator* rpki-validator",
                "cd rpki-validator",
                "mv rpki-validator* rpki-validator.sh",
                "cd preconfigured-tals",
                "wget {}".format(arin_tal),
                "cd ../..",
                "cp -R rpki-validator /usr/bin/rpki-validator"] 
        check_call("&& ".join(cmds), shell=True)



    def _install_bgpscanner(self):
        """Installs bgpscanner and moves to /usr/bin/bgpscanner"""

        self._remove("bgpscanner/")

        cmds = ["sudo apt install meson",
                "sudo apt install zlib1g",
                "sudo apt install zlib1g-dev",
                "sudo apt-get install libbz2-dev",
                "sudo apt-get install liblzma-dev",
                "sudo apt-get install liblz4-dev",
                "sudo apt-get install ninja-build",
                "pip3 install --user meson",
                "sudo apt-get -y install cmake",
                "git clone https://gitlab.com/Isolario/bgpscanner.git"]
        check_call("&& ".join(cmds), shell=True)

        path = "bgpscanner/src/mrtdataread.c"
        prepend = '                if ('
        replace = 'rib->peer->as_size == sizeof(uint32_t))'
        replace_with = 'true)'
        self._replace_line(path, prepend, replace, replace_with)

        # Meson refuses to be installed right so:
        cmds = ["python3 -m venv delete_me",
                "delete_me/bin/pip3 install meson",
                "cd bgpscanner",
                "mkdir build && cd build",
                "../../delete_me/bin/meson ..",
                "cd ../../"]
        check_call("&& ".join(cmds), shell=True)
        cmds = ["cd bgpscanner/build",
                "sudo ninja install",
                "sudo ldconfig",
                "rm -rf delete_me"]
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
                "sudo cp bgpdump /usr/bin/bgpdump"]
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
            self.logger.debug("{} not previously installed".format(remove_me))

    def _replace_line(self, path, prepend, line_to_replace, replace_with):
        """Replaces a line withing a file that has the path path"""

        lines = [prepend + x for x in [line_to_replace, replace_with]]
        for line in fileinput.input(path, inplace=1):
            line = line.replace(*lines)
            sys.stdout.write(line)
