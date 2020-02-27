#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains functions used across classes.

Possible future improvements:
-Move functions that are only used in one file to that file
-Refactor
-Unit tests
"""

from enum import Enum
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
import pytz
from bz2 import BZ2Decompressor
from bs4 import BeautifulSoup as Soup
from pathos.multiprocessing import ProcessingPool
from contextlib import contextmanager
from multiprocessing import cpu_count, Queue, Process, Manager
from .logger import Thread_Safe_Logger as Logger
from .database import db_connection
from .config import set_global_section_header

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
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
    logger.debug("Created {} pool".format(name))
    yield p
    # Need to clear due to:
    # https://github.com/uqfoundation/pathos/issues/111
    p.close()
    p.join()
    p.clear()

# tqdm fails whenever large multiprocess operations take place
# We don't want 60 print statements every time we run multiprocess things
# So instead I wrote my own progress bar
# This prints a progress bar, func should write to sys.stdout to incriment
# This works well with multiprocessing for our applications
# https://stackoverflow.com/a/3160819/8903959
@contextmanager
def progress_bar(logger, msg, toolbar_width):
    if logger.level <= 20:  # logging.INFO
        sys.stdout.write("{}: {} X/{}".format(datetime.now(),
                                               msg,
                                               toolbar_width))
        sys.stdout.write("[%s]" % (" " * toolbar_width))
        sys.stdout.flush()
        # return to start of line, after '['
        sys.stdout.write("\b" * (toolbar_width+1))
    yield
    if logger.level <= 20:
        sys.stdout.write("]\n")

class Enumerable_Enum(Enum):
    # https://stackoverflow.com/a/54919285
    @classmethod
    def list_values(cls):
        return list(map(lambda c: c.value, cls))

    


def now():
    """Returns current time"""

    # https://stackoverflow.com/a/7065242
    return pytz.utc.localize(datetime.utcnow())


def get_default_start():
    """Gets default start time, used in multiple places."""

    return (now()-timedelta(days=2)).replace(hour=0,
                                             minute=0,
                                             second=0,
                                             microsecond=0).timestamp() - 5


def get_default_end():
    """Gets default end time, used in multiple places."""

    # NOTE: Should use the default start for this method
    return (now()-timedelta(days=2)).replace(hour=23,
                                             minute=59,
                                             second=59,
                                             microsecond=59).timestamp()

def download_file(logger,
                  url,
                  path,
                  file_num=1,
                  total_files=1,
                  sleep_time=0,
                  progress_bar=False):
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
                logger.debug("{} / {} downloaded".format(file_num, total_files))
                if progress_bar:
                    incriment_bar(logger)
                return
        # If there is an error in the download this will be called
        # And the download will be retried
        except Exception as e:
            retries -= 1
            time.sleep(5)
            if retries <= 0:
                logger.error("Failed download {}\nDue to: {}".format(url, e))
                sys.exit(1)

def incriment_bar(logger):
    if logger.level <= 20:  # INFO
        sys.stdout.write("#")
        sys.stdout.flush()
    else:
        sys.stdout.flush()

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


def clean_paths(logger, paths, recreate=True):
    """If path exists remove it, else create it"""

    # If a single path is passed in, convert it to a list
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        try:
            remove_func = os.remove if os.path.isfile(path) else shutil.rmtree
            remove_func(path)
        # Files are sometimes deleted even though they no longer exist
        except AttributeError:
            logger.debug("Attribute error when deleting {}".format(path))
        except FileNotFoundError:
            logger.debug("File not found when deleting {}".format(path))
        except PermissionError:
            logger.warning("Permission error when deleting {}".format(path))

    if recreate:
        for path in paths:
            # Fix this later
            os.makedirs(path, mode=0o777, exist_ok=False)


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

def get_lines_in_file(filename: str) -> int:
    """Returns the number of lines in a given file"""

    with open(filename, 'r') as f:
        for count, line in enumerate(f):
            pass
    return count + 1
