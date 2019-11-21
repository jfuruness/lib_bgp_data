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
2. Then the Relationships_File class is then instantiated
    -Note: You can aggregate relationship data sets, which loops over urls
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


from .relationships_file import Rel_File
from .tables import ROVPP_ASes_Table, ROVPP_AS_Connectivity_Table
from .tables import Peers_Table, Customer_Providers_Table
from .tables import ROVPP_Peers_Table, ROVPP_Customer_Providers_Table
from ..utils import utils, error_catcher, db_connection

__author__ = "Justin Furuness", "Matt Jaccino"
__credits__ = ["Justin Furuness", "Matt Jaccino"]
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
    def parse_files(self, rovpp=False, agg_months=0, url=False):
        """Downloads and parses file

        In depth explanation at top of module. Aggregate months aggregates
        relationship data from x months ago into the same table
        """

        # deletes old tables and creates new ones
        self._init_tables()

        # Init Relationships_File class and parse file
        # This could be multithreaded
        # But it's fast compared to other modules so no need
        for url in self._get_urls(agg_months) if not url else [url]:
            Rel_File(self.path, self.csv_dir,
                     url, self.logger).parse_file(rovpp)
        utils.delete_paths(self.logger, [self.csv_dir, self.path])

        if rovpp:
            # Fills these rov++ specific tables
            with db_connection(ROVPP_ASes_Table, self.logger) as as_table:
                as_table.fill_table()
                # creates and closes table
                ROVPP_AS_Connectivity_Table(self.logger).close()


########################
### Helper Functions ###
########################
    @error_catcher()
    def _get_urls(self, months_back=0):
        """Gets urls to download relationship files and the dates.

        For more in depth explanation see the top of the file
        """

        # Api url
        prepend = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        # Get all html tags that might have links
        _elements = [x for x in utils.get_tags(prepend, 'a')[0]]
        # Gets the last file of all bz2 files
        file_urls = [x["href"] for x in _elements if "bz2" in x["href"]]
        return [prepend + x for x in file_urls[-1 - months_back:]]

    def _init_tables(self):
        """Inititializes table and deletes old ones"""

        for table in [Customer_Providers_Table,
                      Peers_Table,
                      ROVPP_Customer_Providers_Table,
                      ROVPP_Peers_Table]:
            with db_connection(table, self.logger) as db:
                # Clears and then creates new tables
                db.clear_table()
