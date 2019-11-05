#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Relationships_Parser

The purpose of this class is to download the relationship files and
insert the data into a database. This is done through a series of steps.

1. Make an api call to:
    -http://data.caida.org/datasets/as-relationships/serial-2/
    -Handled in _get_url function
    -This will return the url of the file that we need to download
    -In that url we have the date of the file, which is also parsed out
    -The serial 2 dataset is used because it has multilateral peering
    -which appears to be the more complete dataset
2. Then check if the file has already been parsed before
    -Handled in parse_files function
    -If the url date is less than the config file date do nothing
    -Else, parse
    -This is done to avoid unneccesarily parsing files
    -If ROVPP, then download a specific file every time
2. Then the Relationships_File class is then instantiated
3. The relationship file is then downloaded
    -This is handled in the utils.download_file function
4. Then the file is unzipped
    -handled by utils _unzip_bz2
5. The relationship file is then split into two
    -Handled in the Relationships_File class
    -This is done because the file contains both peers and
     customer_provider data.
    -The File itself is a formatted CSV with "|" delimiters
    -Using grep and cut the relationships file is split and formatted
    -This is done instead of regex because it is faster and simpler
6. Then each CSV is inserted into the database
    -The old table gets destroyed first
    -This is handleded in the utils.csv_to_db function
    -This is done because the file comes in CSV format
7. The config is updated with the last date a file was parsed

Design Choices:
    -CSV insertion is done because the relationships file is a CSV
    -Dates are stored and checked to prevent redoing old work

Possible Future Extensions:
    -Add test cases
    -Possibly take out date checking for cleaner code?
     Save very little time
"""


import re
from .relationships_file import Rel_File
from ..utils import utils, Config, error_catcher
from datetime import date, datetime

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Relationships_Parser:
    """This class downloads, parses, and deletes files from Caida

    In depth explanation at the top of modue
    """

    __slots__ = ['path', 'csv_dir', 'logger']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables"""

        # Sets path vars and logger
        utils.set_common_init_args(self, args)

    # Note that the utils.run_parser decorator deletes/creates all paths,
    # records start/end time, and upon end or error deletes everything
    @error_catcher()
    @utils.run_parser()
    def parse_files(self, rovpp=False, url=None):
        """Downloads and parses file

        In depth explanation at top of module
        """

        # For the rovpp simulation, pass in rovpp and a url to use
        if rovpp:
            Rel_File(self.path,
                     self.csv_dir,
                     url,
                     self.logger).parse_file(rovpp)
            return

        # Gets the url and the integer date for the latest file
        url, date = self._get_url()
        # If this is a new file, the config date will be less than the
        # websites file date, and so we renew our data
        config = Config(self.logger)
        if config.last_date < date:
            # Init Relationships_File class and parse file
            Rel_File(self.path, self.csv_dir, url, self.logger).parse_file()
            # Update the last date of the config
            config.update_last_date(date)
        else:
            self.logger.info("old file, not parsing")

    def parse_files_agg(self, months_back=0, rovpp=False):
        """Downloads and parses multiple relationship files to aggregate
        relationship data across multiple timeframes with respect to the
        number of months back passed in as a parameter.
        """

        # Get list of URLs for multiple datasets
        urls = self._get_urls_agg(months_back)
        # Iterate over all URLs
        for url in urls:
            # Initialize Relationship File object and parse file
            Rel_File(self.path, self.csv_dir, url, self.logger).parse_file()

########################
### Helper Functions ###
########################
    @error_catcher()
    def _get_url(self):
        """Gets urls to download relationship files and the dates.

        For more in depth explanation see the top of the file
        """

        # Api url
        url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        # Get all html tags that might have links
        _elements = [x for x in utils.get_tags(url, 'a')[0]]
        # Gets the last file of all bz2 files
        file_url = [x["href"] for x in _elements if "bz2" in x["href"]][-1]
        # Get html of file list
        _pre = [x for x in utils.get_tags(url, 'pre')[0]][0]
        # Get the 'Last Modified' date for all files listed
        _last_modified_dates = [x for x in str(_pre).split()
                                if re.match('\d{2}-\w{3}-\d{4}', x)]
        # Get the 'Last Modified' date for the last bz2 
        # file as a numerical string
        file_last_modified = \
         datetime.strptime(_last_modified_dates[-3], "%d-%b-%Y").date()
        # Returns the url plus the max number (the date) in the url
        return url + file_url, file_last_modified

    @error_catcher()
    def _get_urls_agg(self, months_back=0):
        """Gets URLs to download relationship files for aggregating
        relationship datasets based on the number of months
        """

        # API URL
        url = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        # Get all file URLs from the API
        _files = [x["href"] for x in utils.get_tags(url, 'a')[0]
                  if "bz2" in x["href"]]
        # Make a list for the URLs
        urls = [url + x for x in _files[-1 - months_back:]]
        # Return the file URLs
        return urls
