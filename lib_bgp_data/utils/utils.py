#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains functions used across classes.

Possible future improvements:
-Move functions that are only used in one file to that file
-Refactor
-Unit tests
"""

import requests
import time
import urllib
import shutil
import os
import sys
import functools
from datetime import datetime, timedelta
import csv
import json
from bz2 import BZ2Decompressor
from bs4 import BeautifulSoup as Soup
from pathos.multiprocessing import ProcessingPool
from contextlib import contextmanager
from multiprocessing import cpu_count
from .logger import Thread_Safe_Logger as Logger
from .database import db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

# to prevent circular depencies
@contextmanager
def Pool(logger, threads, multiplier, name):
    """Context manager for pathos ProcessingPool"""

    # Creates a pool with threads else cpu_count * multiplier
    p = ProcessingPool(threads if threads else cpu_count() * multiplier)
    logger.info("Created {} pool".format(name))
    yield p
    # Need to clear due to:
    # https://github.com/uqfoundation/pathos/issues/111
    p.close()
    p.join()
    p.clear()


# This decorator wraps any run parser function
# This starts the parser, cleans all paths, ends the parser, and records time
# The point of this decorator is to make sure the parser runs smoothly
def run_parser(paths=True):
    def my_decorator(run_parser_func):
        @functools.wraps(run_parser_func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator

            # Gets the start time
            start_time = now()
            if paths:
                # Deletes everything from and creates paths
                clean_paths(self.logger, [self.path, self.csv_dir])
            try:
                # Runs the parser
                return run_parser_func(self, *args, **kwargs)
            # Upon error, log the exception
            except Exception as e:
                self.logger.error(e)
                raise e
            # End the parser to delete all files and directories always
            finally:
                # Clean up don't be messy yo
                end_parser(self, start_time, paths)
                    
        return function_that_runs_func
    return my_decorator


def now():
    """Returns current time"""

    return datetime.utcnow()


def get_default_start():
    """Gets default start time, used in multiple places."""

    return (now()-timedelta(days=2)).replace(hour=0,
                                             minute=0,
                                             second=0,
                                             microsecond=0).timestamp()


def get_default_end():
    """Gets default end time, used in multiple places."""

    # Note: This replaces time to be at beginning of day because
    # the Caida API is actually broken. We've contacted them but
    # they have not fixed it even though they admitted it was incorrect

    return (now()-timedelta(days=2)).replace(hour=23,
                                             minute=59,
                                             second=59,
                                             microsecond=59).timestamp()

def set_common_init_args(self, args, paths=True):
    """Sets self attributes for arguments common across many classes"""

    # The class name. This because when parsers are done,
    # they aggressively clean up. We do not want parser to clean up in
    # the same directories and delete files that others are using
    name = self.__class__.__name__

    self.logger = args.get("logger") if args.get("logger") else\
        Logger(args)

    if paths:
        # Path to where all files willi go. It does not have to exist
        self.path = args.get("path") if args.get("path") else\
            "/tmp/bgp_{}".format(name)
        self.csv_dir = args.get("csv_dir") if args.get("csv_dir") else\
            "/dev/shm/bgp_{}".format(name)
        clean_paths(self.logger, [self.path, self.csv_dir])

    # Deletes and creates dirs from fresh
    self.logger.debug("Initialized {} at {}".format(name, now()))


def download_file(logger, url, path, file_num=1, total_files=1, sleep_time=0):
    """Downloads a file from a url into a path."""

    logger.debug("Downloading a file.\n    Path: {}\n    Link: {}\n"
                 .format(path, url))

    # This is to make sure that the network is not bombarded with requests
    time.sleep(sleep_time)
    retries = 10

    while retries > 0:
        try:
            # Code for downloading files off of the internet
            with urllib.request.urlopen(url, timeout=60)\
                    as response, open(path, 'wb') as out_file:
                # Copy the file into the specified file_path
                shutil.copyfileobj(response, out_file)
                logger.info("{} / {} downloaded".format(file_num, total_files))
                return
        # If there is an error in the download this will be called
        # And the download will be retried
        except Exception as e:
            retries -= 1
            time.sleep(5)
            if retries <= 0:
                logger.error("Failed download {}\nDue to: {}".format(url, e))
                sys.exit(1)


def delete_paths(logger, paths):
    """Removes directory if directory, or removes path if path"""

    # For unit tests
    if logger is None:
        logger = Logger()

    if not paths:
        paths = []
    # If a single path is passed in, convert it to a list
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        try:
            # If the path is a file
            if os.path.isfile(path):
                # Delete the file
                os.remove(path)
            # If the path is a directory
            if os.path.isdir(path):
                # rm -rf the directory
                shutil.rmtree(path)
        # Just in case we always delete everything at the end of a run
        # So some files may not exist anymore
        except AttributeError:
            logger.debug("Attribute error when deleting {}".format(path))
        except FileNotFoundError:
            logger.debug("File not found when deleting {}".format(path))
        except PermissionError:
            logger.warning("Permission error when deleting {}".format(path))


def clean_paths(logger, paths):
    """If path exists remove it, else create it"""

    delete_paths(logger, paths)
    for path in paths:
        # Yes I know this is a security flaw, but
        # Everything is becoming hacky since we need to demo soon
        # We can fix it later
        # No really, I mean it
        # For real, I will fix it
        # Hahaha I hate selinux
        # Where am I?
        os.makedirs(path, mode=0o777, exist_ok=False)


def end_parser(self, start_time, has_paths=True):
    """To be run at the end of every parser, deletes paths and prints time"""

    if has_paths:
        delete_paths(self.logger, [self.path, self.csv_dir])
    name = self.__class__.__name__
    current = now()
    # https://www.geeksforgeeks.org/python-difference-between-two-dates-in-minutes-using-datetime-timedelta-method/
    minutes, seconds = divmod((current - start_time).total_seconds(), 60)
    self.logger.info("{} ran for {} minutes {} seconds".format(name, minutes, seconds))


def unzip_bz2(logger, old_path):
    """Unzips a bz2 file from old_path into new_path and deletes old file"""

    new_path = "{}.decompressed".format(old_path[:-4])
    with open(new_path, 'wb') as new_file, open(old_path, 'rb') as file:
        decompressor = BZ2Decompressor()
        for data in iter(lambda: file.read(100 * 1024), b''):
            new_file.write(decompressor.decompress(data))

    logger.debug("Unzipped a file: {}".format(old_path))
    delete_paths(logger, old_path)
    return new_path


def write_csv(logger, rows, csv_path):
    """Writes rows into csv_path, a tab delimited csv"""

    logger.debug("Writing to {}".format(csv_path))
    delete_paths(logger, csv_path)

    with open(csv_path, mode='w') as temp_csv:
        csv_writer = csv.writer(temp_csv,
                                delimiter='\t',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
        # Writes all the information to a csv file
        # Writing to a csv then copying into the db
        # is the fastest way to insert files
        csv_writer.writerows(rows)


def csv_to_db(logger, Table, csv_path, clear_table=False):
    """Copies csv into table and deletes csv_path

    Copies tab delimited csv into table and deletes csv_path
    Table should inherit from Database class and have name attribute and
    columns attribute"""

    with db_connection(Table, logger) as t:
        if clear_table:
            t.clear_table()
            t._create_tables()
        logger.debug("Copying {} into the database".format(csv_path))
        # Opens temporary file
        with open(r'{}'.format(csv_path), 'r') as f:
            # Copies data from the csv to the db, this is the fastest way
            t.cursor.copy_from(f, t.name, sep='\t', columns=t.columns, null="")
            t.cursor.execute("CHECKPOINT;")
    logger.debug("Done inserting {} into the database".format(csv_path))
    delete_paths(logger, csv_path)


def rows_to_db(logger, rows, csv_path, Table, clear_table=True):
    """Writes rows to csv and from csv to database"""

    write_csv(logger, rows, csv_path)
    csv_to_db(logger, Table, csv_path, clear_table)


def get_tags(url, tag):
    """Gets the html of a given url, and returns a list of tags"""

    response = requests.get(url)
    # Raises an exception if there was an error
    response.raise_for_status()
    # Get all tags within the beautiful soup from the html and return them
    return [x for x in Soup(response.text, 'html.parser').select(tag)],\
        response.close()


def get_json(url, headers={}):
    """Gets the json from a url"""

    # Formats request
    req = urllib.request.Request(url, headers=headers)
    # Opens request
    with urllib.request.urlopen(req) as url:
        # Gets data from the json in the url
        return json.loads(url.read().decode())
