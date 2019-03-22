#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains functions used across classes"""

import time
import urllib
import shutil
import os
import sys
from datetime import datetime
import csv
from bz2 import BZ2Decompressor


__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# This decorator wraps any run parser function
# This starts the parser, cleans all paths, ends the parser, and records time
# The point of this decorator is to make sure the parser runs smoothly
def run_parser(paths):
    def my_decorator(run_parser_func):
        @functools.wraps(run_parser_func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator

            # Gets the start time
            start_time = datetime.now()
            # Deletes everything from and creates paths
            clean_paths(self.logger, paths)
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
                utils.end_parser(self.logger, paths, start_time)
        return function_that_runs_func
    return my_decorator







def download_file(logger, url, path, file_num, total_files, sleep_time=0):
    """Downloads a file from a url into a path"""

    logger.info("Downloading a file.\n    Path: {}\n    Link: {}\n"
        .format(path, url))

    # This is to make sure that the network is not bombarded with requests or else it breaks
    time.sleep(sleep_time)
    retries = 10

    while retries > 0:
        try:
            # Code for downloading files off of the internet
            with urllib.request.urlopen(url, timeout=60)\
                    as response, open(path, 'wb') as out_file:
                # Copy the file into the specified file_path
                shutil.copyfileobj(response, out_file)
                logger.info("{} / {} downloaded".format(num, total_files))
                return
        # If there is an error in the download this will be called
        # And the download will be retried
        except Exception as e:
            retries -= 1
            time.sleep(5)
            if retries <= 0:
                logger.error("Failed download {}\n because of:".format(url, e))
                sys.exit(1)

def delete_paths(logger, paths):
    """Removes directory if directory, or removes path if path"""

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
            logger.debug(
                "File caused attribute error {}".format(path))
        except FileNotFoundError:
            logger.debug("File not found {}".format(path))

def clean_paths(logger, paths, end=False):
    """If path exists remove it, else create it"""

    delete_paths(logger, paths)
    if not end:
        for path in paths:
            os.makedirs(path)

def end_parser(logger, paths, start_time):
    """To be run at the end of every parser, deletes paths and prints time"""

    delete_paths(logger, paths)
    self.logger.info("Parser started at {}".format(start_time))
    self.logger.info("Parser completed at {}".format(datetime.now())

def unzip_bz2(logger, old_path, new_path):
    """Unzips a bz2 file from old_path into new_path and deletes old file"""

    with open(path, 'wb') as new_file, open(old_path, 'rb') as file:
        decompressor = BZ2Decompressor()
        for data in iter(lambda: file.read(100 * 1024), b''):
            new_file.write(decompressor.decompress(data))

    logger.debug("Unzipped a file: {}".format(old_path))
    delete_paths(logger, old_path)

def _unzip_gz(logger, old_path, new_path):
    """Unzips a .gz file from old_path into new_path and deletes old file"""

    with gzip.open(old_path, 'rb') as f_in:
        with open(path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    logger.debug("Unzipped a file: {}".format(old_path))
    delete_paths(logger, old_path)

def write_csv(logger, rows, csv_path, files_to_delete=None):
    """Writes rows into csv_path, a tab delimited csv"""

    logger.info("Writing to {}".format(csv_path))
    with open(csv_path, mode='w') as temp_csv:
        csv_writer = csv.writer(temp_csv,
                                delimiter='\t',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
        # Writes all the information to a csv file
        # Writing to a csv then copying into the db
        # is the fastest way to insert files
        csv_writer.writerows(rows)

    # If there are old files that are no longer needed, deleted them
    delete_paths(files_to_delete)

def csv_to_db(logger, table, csv_path):
    """Copies csv into table and deletes csv_path

    Copies tab delimited csv into table and deletes csv_path
    Table should inherit from Database class and have name attribute and
    columns attribute"""

    logger.info("Copying {} into the database".format(self.csv_path))
    # Opens temporary file
    f = open(r'{}'.format(csv_path), 'r')

    # Copies data from the csv to the db, this is the fastest way
    table.cursor.copy_from(f, table.name, sep='\t', columns=table.columns)

    # Closes file
    f.close()
    # Closes db connection
    db.close()
    self.logger.info("Done inserting {} into the database".format(csv_path))
    delete_paths(csv_path)

def get_tags( url, tag):
    """Gets the html of a given url, and returns a list of tags"""

    response = requests.get(url)
    # Raises an exception if there was an error
    response.raise_for_status()
    # Creates a beautiful soup object from the get request
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    # Create a list of tags from the html and return them
    return [x for x in soup.select(tag)]