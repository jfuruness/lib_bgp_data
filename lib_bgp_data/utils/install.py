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
from getpass import getpass
from subprocess import check_call, call
import os
from multiprocess import cpu_count
import fileinput
import sys
from .logger import Thread_Safe_Logger as logger, error_catcher
from .config import Config
from .utils import delete_paths

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# This decorator deletes paths before and after func is called
def delete_files(files=[]):
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator
            delete_paths(self.logger, files)
            stuff = func(self, *args, **kwargs)
            delete_paths(self.logger, files)
            return stuff
        return function_that_runs_func
    return my_decorator


# Global is used for decorator
sql_install_file = "/tmp/db_install.sql"


class Install:
    """Installs and configures the lib_bgp_data package"""

    __slots__ = ['logger', 'db_pass']

    @error_catcher()
    def __init__(self):
        """Makes sure that you are a sudo user"""

        class NotSudo(Exception):
            pass

        DEBUG = 10  # Cannot import logging due to deadlocks
        # Initializes self.logger
        self.logger = logger({"stream_level": DEBUG})
        # Makes sure that you are a sudo user
        if os.getuid() != 0:
            raise NotSudo("Sudo priveleges are required for install")

    @error_catcher()
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
            Config(self.logger).create_config(self.db_pass)
            self._create_database()
        # Set unhinged to true to prevent automated writes to disk
        self._modify_database()
        self._install_forecast_extrapolator()
        self._install_rovpp_extrapolator()
        self._install_bgpscanner()
        self._install_bgpdump()
        self._install_rpki_validator()

    # Must remove that file due to password change history
    @error_catcher()
    @delete_files([sql_install_file, "/var/lib/postgresql/.psql_history"])
    def _create_database(self):
        """Creates the bgp database and bgp_user and extensions."""

        # SQL commands to write
        sqls = ["DROP DATABASE bgp;",
                "DROP OWNED BY bgp_user;",
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
        self._run_sql_file(sqls)
        # Must do this here, nothing else seems to create it
        create_extension_args = ('sudo -u postgres psql -d bgp'
                                 ' -c "CREATE EXTENSION btree_gist;"')
        # Allow for failures in case it's already there
        call(create_extension_args, shell=True)

    @error_catcher()
    @delete_files(sql_install_file)
    def _modify_database(self):
        """Modifies the database for speed.

        Makes it so that the database is optimized for speed. The
        database will be corrupted if there is a crash. These changes
        work at a cluster level, so all databases will be changed.
        """

        ram = Config(self.logger).ram
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

    @error_catcher()
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

    @error_catcher()
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
                "git checkout remotes/origin/rovpp",
                "git checkout -b rovpp"]

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

    @error_catcher()
    @delete_files()
    def _install_rpki_validator(self):
        """Installs RPKI validator with our configs.

        This might break in the future, but we need to do it this way
        for now to be able to do what we want with our own prefix origin
        table.
        """

        delete_paths(self.logger, "/var/lib/rpki-validator-3/")

        rpki_url = ("https://ftp.ripe.net/tools/rpki/validator3/beta/generic/"
                    "rpki-validator-3-latest-dist.tar.gz")
        arin_tal = ("https://www.arin.net/resources/manage/rpki/"
                    "arin-ripevalidator.tal")
        # This is the java version they use so we will use it
        cmds = ["sudo apt-get -y install openjdk-8-jre",
                "wget {}".format(rpki_url),
                "tar -xvf rpki-validator-3-latest-dist.tar.gz",
                "rm -rf rpki-validator-3-latest-dist.tar.gz",
                "mv rpki-validator* /var/lib/rpki-validator-3",
                "cd /var/lib/rpki-validator-3",
                "cd preconfigured-tals",
                "wget {}".format(arin_tal)]
        check_call("&& ".join(cmds), shell=True)

        # Changes where the file is hosted
        path = "/var/lib/rpki-validator-3/conf/application-defaults.properties"
        prepend = "rpki.validator.bgp.ris.dump.urls="
        replace = ("https://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz,"
                   "https://www.ris.ripe.net/dumps/riswhoisdump.IPv6.gz")
        replace_with = "http://localhost:8000/upo_csv_path.csv.gz"
        self._replace_line(path, prepend, replace, replace_with)

        # Changes the server address
        path = "/var/lib/rpki-validator-3/conf/application.properties"
        prepend = "server.address="
        replace = "localhost"
        replace_with = "0.0.0.0"
        self._replace_line(path, prepend, replace, replace_with)

        # Since I am calling the script from elsewhere these must be
        # absolute paths
        prepend = "rpki.validator.data.path="
        replace = "."
        replace_with = "/var/lib/rpki-validator-3"
        self._replace_line(path, prepend, replace, replace_with)
 
        prepend = "rpki.validator.preconfigured.trust.anchors.directory="
        replace = "./preconfigured-tals"
        replace_with = "/var/lib/rpki-validator-3/preconfigured-tals"
        self._replace_line(path, prepend, replace, replace_with)

        prepend = "rpki.validator.rsync.local.storage.directory="
        replace = "./rsync"
        replace_with = "/var/lib/rpki-validator-3/rsync"
        self._replace_line(path, prepend, replace, replace_with)

    @error_catcher()
    @delete_files("lzma-dev/")
    def _install_lzma(self):
        """Installs the lzma-dev library which you need for bgpscanner"""

        cmds = ["mkdir lzma-dev",
                "cd lzma-dev/",
                "wget https://tukaani.org/xz/xz-5.2.4.tar.gz",
                "tar -xvf xz-5.2.4.tar.gz",
                "cd xz-5.2.4/",
                "./configure ",
                "make",
                "sudo make install"]

        check_call("&& ".join(cmds), shell=True)

    @error_catcher()
    @delete_files("bgpscanner/")
    def _install_bgpscanner(self):
        """Installs bgpscanner and moves to /usr/bin/bgpscanner"""

        cmds = ["sudo apt -y install meson",
                "sudo apt -y install zlib1g",
                "sudo apt -y install zlib1g-dev",
                "sudo apt-get -y install libbz2-dev",
                "sudo apt-get -y install liblzma-dev",
                "sudo apt-get -y install liblz4-dev",
                "sudo apt-get -y install ninja-build",
                "pip3 install --user meson",
                "sudo apt-get -y install cmake",
                "git clone https://gitlab.com/Isolario/bgpscanner.git"]
        check_call("&& ".join(cmds), shell=True)

        # If this line is not changed it remove improper configurations.
        # We want to keep these because they are included in the monitors
        # Announcements, so they clearly are propogated throughout the
        # internet.
        path = "bgpscanner/src/mrtdataread.c"
        prepend = '                if ('
        replace = 'rib->peer->as_size == sizeof(uint32_t))'
        replace_with = 'true)'
        self._replace_line(path, prepend, replace, replace_with)

        # Meson refuses to be installed right so:
        cmds = ["python3 -m venv delete_me",
                "delete_me/bin/pip3 install wheel",
                "delete_me/bin/pip3 install meson",
                "cd bgpscanner",
                "mkdir build && cd build",
                "../../delete_me/bin/meson ..",
                "cd ../../",
                "cd bgpscanner/build",
                "sudo ninja install",
                "sudo ldconfig",
                "cd ../../",
                "cp bgpscanner/build/bgpscanner /usr/bin/bgpscanner",
                "cp bgpscanner/build/bgpscanner /usr/local/bin/bgpscanner",
                "rm -rf delete_me"]
        check_call("&& ".join(cmds), shell=True)

    @error_catcher()
    @delete_files("bgpdump/")
    def _install_bgpdump(self):
        """Installs bgpdump and moves it to /usr/bin/bgpdump.

        Must be installed from source due to bug fixes not in apt repo.
        """

        # Commands to install from source
        cmds = ["sudo apt -y install mercurial",
                "hg clone https://bitbucket.org/ripencc/bgpdump",
                "cd bgpdump",
                "sudo apt install automake",
                "./bootstrap.sh",
                "make",
                "./bgpdump -T",
                "sudo cp bgpdump /usr/bin/bgpdump",
                "sudo cp bgpdump /usr/local/bin/bgpdump"]
        check_call("&& ".join(cmds), shell=True)

########################
### Helper Functions ###
########################

    @error_catcher()
    @delete_files(sql_install_file)
    def _run_sql_file(self, sqls):
        """Writes sql file"""

        with open(sql_install_file, "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        bash = "sudo -u postgres psql -f {}".format(sql_install_file)
        check_call(bash, shell=True)

    @error_catcher()
    def _replace_line(self, path, prepend, line_to_replace, replace_with):
        """Replaces a line withing a file that has the path path"""

        lines = [prepend + x for x in [line_to_replace, replace_with]]
        for line in fileinput.input(path, inplace=1):
            line = line.replace(*lines)
            sys.stdout.write(line)
