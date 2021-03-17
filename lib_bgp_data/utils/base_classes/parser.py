#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Parser

This class runs all parsers. See README for more details"""


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging
import sys
import os

import pytest
import psycopg2
from subprocess import check_call

from ...utils import utils, config_logging
from ..database import config


class Parser:
    """This class is the base class for all parsers.

    See README for in depth explanation.
    """

    __slots__ = ['path', 'csv_dir', 'kwargs', 'backup_dir', 'name']
    # This will add an error_catcher decorator to all methods

    parsers = []

    # By default, should be false. Subclasses can override this
    backup = False
    # List of all the parsers that should be backed up
    parsers_backup = []

    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses

        This is incredibly useful for a few reasons. Mainly, you can
        strictly enforce proper templating with this. And also, you can
        automatically add all of these things to things like argparse
        calls and such. Very powerful tool.
        """

        super().__init_subclass__(**kwargs)
        cls.parsers.append(cls)

        if cls.backup is True:
            cls.parsers_backup.append(cls)

    def __init__(self, **kwargs):
        """Initializes logger and path variables.

        Section is the arg for the config. You can run on entirely
        separate databases with different sections."""

        section = config.set_global_section_header(kwargs.get("section"))
        kwargs["section"] = kwargs.get("section", section)
        # The class name. This because when parsers are done,
        # they aggressively clean up. We do not want parser to clean up in
        # the same directories and delete files that others are using
        self.name = f"{kwargs['section']}_{self.__class__.__name__}"
        config_logging(kwargs.get("stream_level", logging.INFO),
                       kwargs["section"])

        # Path to where all files willi go. It does not have to exist
        self.path = kwargs.get("path", f"/tmp/{self.name}")
        self.csv_dir = kwargs.get("csv_dir", f"/dev/shm/{self.name}")

        # IS THIS AN APPROPRIATE LOCATION TO STORE BACKUPS???
        self.backup_dir = kwargs.get("backup_dir", f"/data/{self.name}_backups")

        # If parser can be backed up, make sure it has tables class attribute
        if self.backup is True:
            assert hasattr(self, "tables"), ("Please have a class attribute that "
                                             "lists the tables that should be "
                                             "backed up.")

        # Recreates empty directories
        utils.clean_paths([self.path, self.csv_dir])
        self.kwargs = kwargs
        logging.debug(f"Initialized {self.name} at {utils.now()}")
        assert hasattr(self, "_run"), ("Needs _run, see Parser.py's run func "
                                       "Note that this is also used by default"
                                       " for running argparse. The main method"
                                       " for the parser must be labelled run")

    def run(self, *args, **kwargs):
        """Times main function of parser, errors nicely"""

        start_time = utils.now()
        error = False
        try:
            self._run(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            error = True
        finally:
            self.end_parser(start_time, error)

    def end_parser(self, start_time, error: bool):
        """Ends parser, prints time and deletes files"""

        utils.delete_paths([self.path, self.csv_dir])
        # https://www.geeksforgeeks.org/python-difference-between-two-
        # dates-in-minutes-using-datetime-timedelta-method/
        _min, _sec = divmod((utils.now() - start_time).total_seconds(), 60)
        logging.info(f"{self.__class__.__name__} took {_min}m {_sec}s")
        if error:
            sys.exit(1)

    def backup_tables(self):
        """Runs the parser and properly maintains the table(s) that it uses"""

        # Check the tables belonging to specific parser, only parsers with
        # tables class attribute will have this function called
        for table in self.tables:
            backup = os.path.join(self.backup_dir, f'{table.name}.sql.gz')
            with table() as t:
                try:
                    if t.get_count() == 0:
                        raise psycopg2.errors.UndefinedTable()
                except psycopg2.errors.UndefinedTable:
                    from ..database.config import global_section_header as gsh
                    assert gsh is not None
                    if os.path.exists(backup):
                        t.restore_table(gsh, backup)

        # Run the specific parser
        self.run()

        # Back up the tables
        for table in self.tables:
            try:
                self.backup_table(table)
                if "PYTEST_CURRENT_TEST" not in os.environ:
                    subject = (f"Successfully Backed-up {table.name} table "
                               f"at {utils.now()}")

                    # Construct body of email
                    body = f"The {table.name} table was successfully backed-up."

                    # TODO: Send email to maintainers once done testing
                    utils.send_email(subject, body)

            except Exception as e:
                if "PYTEST_CURRENT_TEST" not in os.environ:
                    subject = f"Failed to Backup {table.name} table at {utils.now()}"

                    # Construct body of email
                    body = (f"There was an error backing up the {table.name} "
                            "table. Below are the outputs:\n")
                    if hasattr(e, "stdout"):
                        body += f"STD_OUT Message: {e.stdout}\n"
                    if hasattr(e, "stderr"):
                        body += f"STD_ERR Message: {e.stderr}\n"
                    body += f"Error: {e}"

                    # TODO: Send email to maintainers once done testing
                    utils.send_email(subject, body)

    def backup_table(self, table):
        """Makes a new backup if live table has more data than old backup."""

        prev_backup = os.path.join(self.backup_dir, f'{table.name}.sql.gz')
        tmp_backup = os.path.join(self.backup_dir, 'temp.sql.gz')

        from ..database.config import global_section_header as gsh
        assert gsh is not None
       
        # making the backup directory if doesn't exist. (e.g. first time)
        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)

        # if previous backups don't exists, make backups right now
        prev_existed = os.path.exists(prev_backup)
        if not os.path.exists(prev_backup):
            table.backup_table(table.name, gsh, prev_backup)
 
        # make a temp backup of live table
        table.backup_table(table.name, gsh, tmp_backup)

        with table() as db:
            # copy live table
            db.execute('DROP TABLE IF EXISTS temp')
            db.execute(f'CREATE TABLE temp AS TABLE {table.name}')

            # restore previous backup
            db.restore_table(gsh, prev_backup)
            count_prev = db.get_count()
            
            # restore temp
            db.restore_table(gsh, tmp_backup)
            count_tmp = db.get_count()

            # new backup is larger, save as the most up-to-date backup
            if count_tmp >= count_prev:
                check_call(f'mv {tmp_backup} {prev_backup}', shell=True)
            # restore live table
            db.execute(f'DROP TABLE {table.name}')
            db.execute(f'CREATE TABLE {table.name} AS TABLE temp')
            db.execute('DROP TABLE temp')

            if os.path.exists(tmp_backup):
                os.remove(tmp_backup)

        # If there was a previous backup and count_tmp is not greater than
        # count_prev, then the new backup made does not reflect the new
        # changes that were added into the table.
        if prev_existed and count_tmp < count_prev:
            error_msg = (f"When making the backup for the {table.name} table "
                         "after it was updated, the backup file generated was "
                         "not consistent with the live table. Therefore, the "
                         "previous backup file was not overwritten and does "
                         "not reflect the most updated state of the table.\n"
                         f"Prev Count: {count_prev}\n"
                         f"Current Count: {count_tmp}")
            raise Exception(error_msg)

    @classmethod
    def run_backupables(cls):
        """Run all the parsers that are intended to be automated
        and backed up"""

        def inner_run(*args, **kwargs):
            for p in cls.parsers_backup:
                print(p)
                p().backup_tables()
        return inner_run

    @classmethod
    def argparse_call(cls):
        """This function returns method to override argparse action

        To run a function when argparse is called, you must create an
        argparse.action class. This class must have a __call__ method
        that contains your function. This will return that method so
        that we can dynamically add to the argparse parser args.

        https://stackoverflow.com/a/18431364
        """

        def argparse_call_override(*args, **kwargs):
            cls().run()
        return argparse_call_override
