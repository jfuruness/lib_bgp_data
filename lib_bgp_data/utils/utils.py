#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains functions used across classes"""

__authors__ = ["Justin Furuness", "Matt Jaccino", "Samarth Kasbawala"]
__credits__ = ["Justin Furuness", "Matt Jaccino", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from contextlib import contextmanager
import csv
from datetime import datetime, timedelta
import fileinput
import functools
import json
import logging
from multiprocessing import cpu_count
import os
from subprocess import check_call, DEVNULL
import sys
import time
import smtplib
from email.message import EmailMessage

from bs4 import BeautifulSoup as Soup
from bz2 import BZ2Decompressor
import gzip
from pathos.multiprocessing import ProcessingPool
import pytz
import requests
import urllib
import shutil
from psutil import process_iter
from signal import SIGTERM


# This decorator deletes paths before and after func is called
def delete_files(files=[]):
    """This decorator deletes files before and after a function.

    This is very useful for installation procedures.
    """
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator
            # Delete the files - prob don't exist yet
            delete_paths(files)
            # Run the function
            stuff = func(self, *args, **kwargs)
            # Delete the files if they do exist
            delete_paths(files)
            return stuff
        return function_that_runs_func
    return my_decorator


@contextmanager
def Pool(threads: int, multiplier: int, name: str):
    """Context manager for pathos ProcessingPool"""

    # Creates a pool with threads else cpu_count * multiplier
    p = ProcessingPool(threads if threads else cpu_count() * multiplier)
    logging.debug(f"Created {name} pool")
    yield p
    # Need to clear due to:
    # https://github.com/uqfoundation/pathos/issues/111
    p.close()
    p.join()
    p.clear()


def low_overhead_log(msg: str, level: int):
    """Heavy multiprocessed stuff should not log...

    This is because the overhead is too great, even with
    rotating handlers and so on. To fix this, we impliment this func
    This func by default has level set to None. If level is not None
    we know a heavy multiprocess func is running. If level is debug, we
    print. Otherwise we do not.
    """

    # Not running heavy parallel processes
    if level is None:
        logging.debug(msg)
    # logging.DEBUG is 10, but I can't write that because then
    # it might restart logging again and deadlock
    elif level == 10:
        print(msg)


def write_to_stdout(msg: str, log_level: int, flush=True):
    # Note that we need log level here, since if we are doing
    # This only in heaavily parallel processes
    # For which we do not want the overhead of logging
    if log_level <= 20:
        sys.stdout.write(msg)
        sys.stdout.flush()

# tqdm fails whenever large multiprocess operations take place
# We don't want 60 print statements every time we run multiprocess things
# So instead I wrote my own progress bar
# This prints a progress bar, func should write to sys.stdout to incriment
# This works well with multiprocessing for our applications
# https://stackoverflow.com/a/3160819/8903959
@contextmanager
def progress_bar(msg: str, width: int):
    log_level = logging.root.level
    write_to_stdout(f"{datetime.now()}: {msg} X/{width}",
                    log_level,
                    flush=False)
    write_to_stdout("[%s]" % (" " * width), log_level)
    write_to_stdout("\b" * (width+1), log_level)
    yield
    write_to_stdout("]\n", log_level)


def now():
    """Returns current time"""

    # https://stackoverflow.com/a/7065242
    return pytz.utc.localize(datetime.utcnow())


def get_default_start() -> int:
    """Gets default start time, used in multiple places."""

    return int((now()-timedelta(days=2)).replace(hour=0,
                                                 minute=0,
                                                 second=0,
                                                 microsecond=0
                                                 ).timestamp() - 5)


def get_default_end() -> int:
    """Gets default end time, used in multiple places."""

    # NOTE: Should use the default start for this method
    return int((now()-timedelta(days=2)).replace(hour=23,
                                                 minute=59,
                                                 second=59,
                                                 microsecond=59
                                                 ).timestamp())


def download_file(url: str,
                  path: str,
                  file_num=1,
                  total_files=1,
                  sleep_time=0,
                  progress_bar=False,
                  verify=True):
    """Downloads a file from a url into a path.
       Verify: SSL certificate"""

    log_level = logging.root.level
    if progress_bar:  # mrt_parser or multithreaded app running, disable log
        logging.root.handlers.clear()
        logging.shutdown()
    low_overhead_log(f"Downloading\n  Path:{path}\n Link:{url}\n", log_level)
    # This is to make sure that the network is not bombarded with requests
    time.sleep(sleep_time)
    retries = 10

    while retries > 0:
        try:
            # Code for downloading files off of the internet
            import ssl
            ctx = ssl._create_unverified_context() if verify \
                    else ssl.create_default_context()

            with urllib.request.urlopen(url, timeout=60, context=ctx)\
                    as response, open(path, 'wb') as out_file:
                # Copy the file into the specified file_path
                shutil.copyfileobj(response, out_file)
                low_overhead_log(f"{file_num} / {total_files} downloaded",
                                 log_level)
                if progress_bar:
                    incriment_bar(log_level)
                return
        # If there is an error in the download this will be called
        # And the download will be retried
        except Exception as e:
            retries -= 1
            time.sleep(5)
            if retries <= 0 or "No such file" in str(e):
                logging.error(f"Failed download {url}\nDue to: {e}")
                sys.exit(1)


def incriment_bar(log_level: int):
    # Needed here because mrt_parser can't log
    if log_level <= 20:  # INFO
        sys.stdout.write("#")
        sys.stdout.flush()
    else:
        sys.stdout.flush()


def delete_paths(paths):
    """Removes directory if directory, or removes path if path"""

    if not paths:
        paths = []
    # If a single path is passed in, convert it to a list
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        try:
            remove_func = os.remove if os.path.isfile(path) else shutil.rmtree
            remove_func(path)
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
            logging.debug(f"Attribute error when deleting {path}")
        except FileNotFoundError:
            logging.debug(f"File not found when deleting {path}")
        except PermissionError:
            logging.warning(f"Permission error when deleting {path}")


def clean_paths(paths):
    """If path exists remove it, else create it"""

    # If a single path is passed in, convert it to a list
    if not isinstance(paths, list):
        paths = [paths]
    delete_paths(paths)
    for path in paths:
        # Fix this later
        os.makedirs(path, mode=0o777, exist_ok=False)


def unzip_bz2(old_path: str) -> str:
    """Unzips a bz2 file from old_path into new_path and deletes old file"""

    new_path = f"{old_path[:-4]}.decompressed"
    with open(new_path, 'wb') as new_file, open(old_path, 'rb') as file:
        decompressor = BZ2Decompressor()
        for data in iter(lambda: file.read(100 * 1024), b''):
            new_file.write(decompressor.decompress(data))

    logging.debug(f"Unzipped a file: {old_path}")
    delete_paths(old_path)
    return new_path

def unzip_gz(path):
    # https://stackoverflow.com/a/44712152/8903959
    with gzip.open(path, 'rb') as f_in:
        with open(path.replace(".gz", ""), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

def write_csv(rows: list, csv_path: str):
    """Writes rows into csv_path, a tab delimited csv"""

    logging.debug(f"Writing to {csv_path}")
    delete_paths(csv_path)

    with open(csv_path, mode='w') as temp_csv:
        csv_writer = csv.writer(temp_csv,
                                delimiter='\t',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
        # Writes all the information to a csv file
        # Writing to a csv then copying into the db
        # is the fastest way to insert files
        csv_writer.writerows(rows)


def csv_to_db(Table, csv_path: str, clear_table=False):
    """Copies csv into table and deletes csv_path

    Copies tab delimited csv into table and deletes csv_path
    Table should inherit from Database class and have name attribute and
    columns attribute

    NOTE: I know there is a csv_dict_writer or something like that. However
    I think because we do this on such a massive scale, this will surely be
    slower, and the columns should always remain the same. So for speed,
    we just use list of lists of rows to copy, not list of dicts of rows."""

    with Table() as t:
        if clear_table:
            t.clear_table()
        t._create_tables()
        # No logging for mrt_announcements, overhead slows it down too much
        logging.debug(f"Copying {csv_path} into the database")
        try:
            # Opens temporary file
            with open(r'{}'.format(csv_path), 'r') as f:
                columns = [x for x in t.columns if x != "id"]
                # Copies data from the csv to the db, this is the fastest way
                t.cursor.copy_from(f, t.name, sep='\t', columns=columns, null="")
                t.cursor.execute("CHECKPOINT;")
        except Exception as e:
            print(e)
            print(csv_path)
            input()
            raise e
        # No logging for mrt_announcements, overhead slows it down too much
        logging.debug(f"Done inserting {csv_path} into the database")
    delete_paths(csv_path)


def rows_to_db(rows: list, csv_path: str, Table, clear_table=True):
    """Writes rows to csv and from csv to database"""

    write_csv(rows, csv_path)
    csv_to_db(Table, csv_path, clear_table)


def get_tags(url: str, tag: str, verify=True):
    """Gets the html of a given url, and returns a list of tags"""

    # SHOULD NOT HAVE NO VERIFY BUT ISOLARIO GIVING SSL ERRORS
    response = requests.get(url, verify=verify)
    # Raises an exception if there was an error
    response.raise_for_status()
    # Get all tags within the beautiful soup from the html and return them
    tags = [x for x in Soup(response.text, 'html.parser').select(tag)]
    response.close()

    return tags


def get_json(url: str, headers={}):
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


def run_cmds(cmds, timeout=None):

    cmd = " && ".join(cmds) if isinstance(cmds, list) else cmds

    kwargs = {"shell": True}

    # If logging is greater than or equal to info
    if logging.root.level >= 20:
        kwargs.update({"stdout": DEVNULL, "stderr": DEVNULL})
    if timeout is not None:
        kwargs["timeout"] = timeout

    logging.debug(f"Running: {cmd}")
    check_call(cmd, **kwargs)


def replace_line(path, prepend, line_to_replace, replace_with):
    """Replaces a line withing a file that has the path path"""

    lines = [prepend + x for x in [line_to_replace, replace_with]]
    for line in fileinput.input(path, inplace=1):
        line = line.replace(*lines)
        sys.stdout.write(line)

def send_email(subject, body, recipients=[]):
    """Sends an email notification"""

    # Get the adress and password from the environment variables
    email_address = os.environ.get("BGP_EMAIL_USER")
    password = os.environ.get("BGP_EMAIL_PASS")

    assert isinstance(recipients, list)

    # Build the message
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_address
    message["To"] = ", ".join([email_address] + recipients)
    message.set_content(body)

    # Send the message
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_address, password)
        smtp.send_message(message)

def kill_port(port: int, wait: bool = True):
    for proc in process_iter():
        for conns in proc.connections(kind='inet'):
            if conns.laddr.port == port:
                proc.send_signal(SIGTERM) # or SIGKILL
                # Sometimes the above doesn't do it's job
                run_cmds(f"sudo kill -9 $(lsof -t -i: {port})")
    if wait:
        time.sleep(120)

def add_cronjob(name, time, executable, overwrite=False):
    """Creates a cronjob of name, that runs executable at (cron) time."""
    cronjob = f'/etc/cron.d/{name}'
    if not os.path.exists(cronjob) or overwrite:
        run_cmds(f'echo "{time} root {executable}" > {cronjob}')
