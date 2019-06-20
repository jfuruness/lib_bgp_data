#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Install.

The Install class contains the functionality to create through a script
everything that is needed to be used for the program to run properly.
This is done through a series of steps.

1. Create the config file.

1. Initialize the MRT_File class
2. The MRT File will be downloaded from the MRT_Parser using utils
3. Parse the MRT_File using bgpscanner and sed
    -bgpscanner is used because it is the fastest BGP dump scanner
    -bgpscanner ignores announcements with malformed attributes
    -bgpdump can be used for full runs to include announcements with
     malformed attributes, because some ASs do not ignore them
    -sed is used because it is cross compatable and fast
        -Must use regex parser that can find/replace for array format
    -Possible future extensions:
        -Use a faster regex parser?
        -Add parsing updates functionality?
3. Parse the MRT_File into a CSV
    -Handled in _bgpdump_to_csv function
    -This is done because there are 30-100GB of data
    -Fast insertion is needed, bulk insertion is the fastest
        -CSV is fastest insertion method, second only to binary
        -Binary insertion isn't cross compatable with postgres versions
    -Delete old files
4. Insert the CSV file into the database using COPY and then deleted
    -Handled in parse_file function
    -Unnessecary files deleted for space

Design choices (summarizing from above):
    -bgpscanner is the fastest BGP dump scanner so it is used to parse
    -bgpscanner ignores announcements with malformed attributes
    -bgpdump can be used for full runs since it does not ignore
     malformed announcements, which some AS's do not ignore
    -sed is used for regex parsing because it is fast and portable
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files

Possible Future Extensions:
    -Add functionality to download and parse updates?
    -Test different regex parsers other than sed for speed?
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
    """Installs stuff"""

    __slots__ = ['logger', 'db_pass']

    @error_catcher()
    def __init__(self):
        """Create a new connection with the databse"""

        class NotSudo(Exception):
            pass

        # Initializes self.logger
        self.logger = logger({"stream_level": DEBUG})
        if os.getuid() != 0:
            raise NotSudo("Sudo priveleges are required for install")
        self.db_pass = getpass("Password for database: ")

    @error_catcher()
    def install(self,
                exr_path="/home/jmf/forecast-extrapolator",
                rovpp_exr_path="/home/jmf/rovpp-extrapolator",
                unhinged=False):
        """Installs everything"""

        Config(self.logger).create_config(self.db_pass,
                                          exr_path,
                                          rovpp_exr_path)
        self._create_database()
        self._modify_database(unhinged)
        self._install_extrapolator(exr_path, rovpp_exr_path)

    @error_catcher()
    def _create_database(self):
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
        with open("/tmp/db_install.sql", "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        commands = ["sudo -u postgres psql -f /tmp/db_install.sql",
                    "rm /var/lib/postgresql/.psql_history"]
        call("; ".join(commands), shell=True)
        os.remove("/tmp/db_install.sql")

    @error_catcher()
    def _modify_database(self, unhinge=False):
        """NOTE: SOME OF THESE CHANGES WORK AT A CLUSTER LEVEL, SO ALL DBS WILL BE CHANGED!!!"""
        """NOTE that if server goes down this may cause corruption"""

        ram = int(input("What is the amount of ram on the system in MB? "))
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
                # https://www.postgresql.org/docs/current/runtime-config-resource.html
                # https://dba.stackexchange.com/a/18486
                # https://severalnines.com/blog/setting-optimal-environment-postgresql
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
                # https://www.2ndquadrant.com/en/blog/basics-of-tuning-checkpoints/
                # manually do all checkpoints to abuse this thing
                "ALTER SYSTEM SET checkpoint_timeout TO '1d';",
                "ALTER SYSTEM SET checkpoint_completion_target TO .9;",
                # The amount of ram that needs to be hit before a write do disk
                "ALTER SYSTEM SET max_wal_size TO '{}MB';".format(ram-1000),
                # Disable autovaccum
                "ALTER SYSTEM SET autovacuum TO off;",
                # Change max number of workers - since this is now manual it can be higher
                "ALTER SYSTEM SET autovacuum_max_workers TO {};".format(cpu_count() - 1),
                # Change the number of max_parallel_maintenance_workers - since its manual it can be higher
                "ALTER SYSTEM SET max_parallel_maintenance_workers TO {};".format(cpu_count() - 1),
                "ALTER SYSTEM maintenance_work_mem TO '{}MB';".format(int(ram/5))])
                # Yes I know I could call this, but this is just for machines that might not have it or whatever
                #stack_limit = int(input("What is the output of ulimit -s?"))
                # https://www.postgresql.org/docs/9.1/runtime-config-resource.html
                
                #"ALTER SYSTEM SET max_stack_depth TO '{}MB';".format(int(stack_limit/1024)-1)]

        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_mod_file.write(sql + "\n")
        call("sudo -u postgres psql -f /tmp/db_modify.sql", shell=True)
        os.remove("/tmp/db_modify.sql")

    @error_catcher()
    def _install_extrapolator(self, exr_path, rovpp_exr_path):
        input("About to delete BGPExtrapolator if exists, press any key")
        try:
            rmtree("BGPExtrapolator/")
        except FileNotFoundError:
            self.logger.debug("Extrapolator was not previouslt installed")
        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator/Misc",
                "sudo ./apt-install-deps.sh",
                "sudo apt install libboost-test-dev",
                "cd ..",
                "make -j{}".format(cpu_count()),
                "cp bgp-extrapolator {}".format(exr_path),
                "git checkout remotes/origin/rovpp",
                "git checkout -b rovpp"]
        check_call("; ".join(cmds), shell=True)

        for line in fileinput.input("BGPExtrapolator/SQLQuerier.cpp",
                                    inplace=1):
            line = line.replace('    string file_location = "./bgp.conf";',
                                '    string file_location = "/etc/bgp/bgp.conf";')
            sys.stdout.write(line)
                
        cmds = ["cd BGPExtrapolator",
                "make -j{}".format(cpu_count()),
                "cp bgp-extrapolator {}".format(rovpp_exr_path)]

        check_call("; ".join(cmds), shell=True)
