#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Install that installs everything"""

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
    def install(self):
        """Installs everything"""

        self._create_config()
        self._create_database()
        self._modify_database()

    @error_catcher()
    def _create_config(self):
        """Creates config file"""

        conf_lines = ["[bgp]",
                      "host = localhost",
                      "database = bgp",
                      "password = {}".format(self.db_pass),
                      "user = bgp_user",
                      "last_relationship_update = 0"]

        try:
            os.mkdir("/etc/bgp")
        except FileExistsError:
            # MOVE! GET OUT OF THE WAY!!!
            shutil.rmtree("/etc/bgp")
            os.mkdir("etc/bgp")
        with open("/etc/bgp/bgp.conf", "w+") as conf:
            for line in conf_lines:
                conf.write(line + "\n")

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
    def _modify_database(self):
        """NOTE: SOME OF THESE CHANGES WORK AT A CLUSTER LEVEL, SO ALL DBS WILL BE CHANGED!!!"""

        sqls = ["CREATE EXTENSION IF NOT EXISTS btree_gist;",
                "ALTER SYSTEM SET fsync TO off;",
                "ALTER SYSTEM SET synchronous_commit TO off;",
                "ALTER SYSTEM SET full_page_writes TO off;",
                "

        # for later: shared buffers. temp_buffers, work_mem, maintenance_work_mem, autovacuum_work_mem, max_stack_depth,#max_worker_processes = 8               # (change requires restart)
#max_parallel_maintenance_workers = 2   # taken from max_parallel_workers
#max_parallel_workers_per_gather = 2    # taken from max_parallel_workers
#max_parallel_workers = 8               # maximum number of max_worker_processes that
checkpoint_timeout = 30min              # range 30s-1d
max_wal_size = 5GB
min_wal_size = 80MB
random page cost???
effective cache size
#autovacuum = on                        # Enable autovacuum subprocess?  'on'
                                        # requires track_counts to also be on.
#autovacuum_max_workers = 3             # max number of autovacuum subprocesses
                                        # (change requires restart)

