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

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from getpass import getpass
from subprocess import call
import os
from .utils import ThreadSafeLogger as logger
from .utils import Config

class Install:
    """Installs stuff"""

    __slots__ = ['logger', 'db_pass']

    @error_catcher()
    def __init__(self):
        """Create a new connection with the databse"""

        # Initializes self.logger
        self.logger = logger()
        self.db_pass = getpass("Password for database: ")

    @error_catcher()
    def install(self, unhinged=False):
        """Installs everything"""

        Config(self.logger).create_config(input("db password: "))
        self._create_database()
        self._modify_database(unhinged)
        self._install_extrapolator()

    @error_catcher()
    def _create_datase(self):
        sqls = ["CREATE DATABASE bgp;",
                "CREATE USER bgp_user;",
                "REVOKE CONNECT ON DATABASE bgp FROM PUBLIC;"
                "REVOKE ALL ON ALL TABLES IN SCHEMA public TO bgp_user;",
                "GRANT ALL PRIVILEGES ON DATBASE bgp TO bgp_user;",
                """GRANT ALL PRIVILEGES ON ALL SEQUENCES
                IN SCHEMA public TO bgp_user;""",
                "ALTER USER bgp_user WITH PASSWORD {}".format(self.db_pass),
                "ALTER USER bgp_user WITH SUPERUSER"]
        with open("/tmp/db_install.sql", "w+") as db_install_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        commands = ["sudo -i -u postgres",
                    "psql -f /tmp/db_install.sql",
                    "rm ~/.psql_history"]
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
                "ALTER SYSTEM SET max_parallel_workers TO {}".format(
                    cpu_count() - 1),
                "ALTER SYSTEM SET max_worker_processes TO {}".format(
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
                "ALTER SYSTEM SET effective_cache_size TO '{}MB'".format(ram),
                # Set random page cost to 2 if no ssd, with ssd
                # seek time is one for ssds
                "ALTER SYSTEM SET random_page_cost TO {}".format(
                    float(input("If SSD, enter 1, else enter 2")))]
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
                "ALTER SYSTEM SET max_parallel_maintenance_workers TO {};".format(cpu_count() - 1)
                # Alter the amount of parallel workers
                "ALTER SYSTEM SET max_parallel_mainenance_workers TO {};".format(cpu_count() - 1),
                "ALTER SYSTEM maintenance_work_mem TO '{}MB';".format(int(ram/5)),
                # Yes I know I could call this, but this is just for machines that might not have it or whatever
                stack_limit = int(input("What is the output of ulimit -s?"))
                # https://www.postgresql.org/docs/9.1/runtime-config-resource.html
                "ALTER SYSTEM SET max_stack_depth TO '{}MB';".format(int(stack_limit/1024)-1)]

        with open("/tmp/db_modify.sql", "w+") as db_mod_file:
            for sql in sqls:
                db_install_file.write(sql + "\n")
        commands = ["sudo -i -u postgres",
                    "psql -f /tmp/db_install.sql",
                    "rm ~/.psql_history"]
        call("; ".join(commands), shell=True)
        os.remove("/tmp/db_install.sql")

    @error_catcher()
    def _install_extrapolator(self):
        # Install extrapolator and move executable
        # delete github repo lmaoooo
        # cd into extrapolator and git checkout remotes/origin/rovpp
        # git checkout -b rovpp
        # vim SQLQuerier.cpp
        # line 302 change path to be "/etc/bgp/bgp.conf"
        # make -j12
        # Move executable somewhere else and call it rovpp

        # Put both of the paths into the /etc/bgp.conf file
        # WHEN MAKE CONFIG FILE MUST OUT THSI INFO IN THERE!!!
