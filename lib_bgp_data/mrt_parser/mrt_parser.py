#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Parser

The purpose of this class is to download the mrt files and insert them
into a database. This is done through a series of steps.

1. Make an api call to https://bgpstream.caida.org/broker/data
    -Handled in _get_mrt_urls function
    -This will return json for rib files which contain BGP announcements
    -From this we parse out urls for the BGP dumps
    -This only returns the first dump for the time interval given
        -However, we only want one dump, multiple dumps would have
         data that conflicts with one another
        -For longer intervals use one BGP dump then updates
2. Then all the mrt files are downloaded in parallel
    -Handled in _multiprocess_download function
    -This instantiates the mrt_file class with each url
        -utils.download_file handles downloading each particular file
    -Four times the CPUs is used for thread count since it is I/O bound
        -Mutlithreading with GIL lock is better than multiprocessing
         since this is just intesive I/O in this case
    -Downloaded first so that we parse the largest files first
    -In this way, more files are parsed in parallel (since the largest
     files are not left until the end)
3. Then all mrt_files are parsed in parallel
    -Handled in _multiprocess_parse_dls function
    -The mrt_files class handles the actual parsing of the files
    -CPUs - 1 is used for thread count since this is a CPU bound process
    -Largest files are parsed first for faster overall parsing
    -bgpscanner is the fastest BGP dump scanner so it is used for tests
    -bgpdump used to be the only parser that didn't ignore malformed
     announcements, but now with a change bgpscanner does this as well
        -This was a problem because some ASes do not ignore these errors
4. Parsed information is stored in csv files, and old files are deleted
    -This is handled by the mrt_file class
    -This is done because there is thirty to one hundred gigabytes
        -Fast insertion is needed, and bulk insertion is the fastest
    -CSVs are chosen over binaries even though they are slightly slower
        -CSVs are more portable and don't rely on postgres versions
        -Binary file insertion relies on specific postgres instance
    -Old files are deleted to free up space
5. CSV files are inserted into postgres using COPY, and then deleted
    -This is handled by mrt_file class
    -COPY is used for speedy bulk insertions
    -Files are deleted to save space
    -Duplicates are not deleted because this is an intensive process
        -There are not a lot of duplicates, so it's not worth the time
        -The overall project takes longer if duplicates are deleted
        -A duplicate has the same AS path and prefix
6. VACUUM ANALYZE is then called to analyze the table for statistics
    -An index is never created on the mrt announcements because when
     the announcements table is intersected with roas table, only a
     parallel sequential scan is used

Design choices (summarizing from above):
    -We only want the first BGP dump
        -Multiple dumps have conflicting announcements
        -Instead, for longer intervals use one BGP dump and updates
    -Due to I/O bound downloading:
        -Multithreading is used over multiprocessing for less memory
        -Four times CPUs is used for thread count
    -Downloading is done and completed before parsing
        -This is done to ensure largest files get parsed first
        -Results in fastest time
    -Downloading completes 100% before parsing because synchronization
     primitives make the program slower if downloading is done until
     threads are available for parsing
    -Largest files are parsed first because due to the difference in
     in file size there is more parallelization achieved when parsing
     largest files first resulting in a faster overall time
    -CPUs - 1 is used for thread count since the process is CPU bound
        -For our machine this is the fastest, feel free to experiment
    -bgpscanner is the fastest BGP dump scanner so it is used for tests
    -bgpdump used to be the only parser that didn't ignore malformed
     announcements, but now with a change bgpscanner does this as well
        -This was a problem because some ASes do not ignore these errors
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files
    -Duplicates are not deleted to save time, since there are very few
        -A duplicate has the same AS path and prefix



Possible Future Extensions:
    -Add functionality to download and parse updates?
        -This would allow for a longer time interval
        -After the first dump it is assumed this would be faster?
        -Would need to make sure that all updates are gathered, not
         just the first in the time interval to the api, as is the norm
    -Test again for different thread numbers now that bgpscanner is used
    -Add test cases
"""


import requests
from datetime import timedelta
from .mrt_file import MRT_File
from ..utils import error_catcher, utils, db_connection
from .tables import MRT_Announcements_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class MRT_Parser:
    """This class downloads, parses, and deletes files from Caida.

    In depth explanation at the top of module.
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'dl_pool', 'p_pool']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        with db_connection(MRT_Announcements_Table, self.logger) as ann_table:
            # Clears the table for insertion
            ann_table.clear_table()
            # Tables can't be created in multithreading so it's done now
            ann_table._create_tables()

    @error_catcher()
    @utils.run_parser()
    def parse_files(self,
                    start=utils.get_default_start(),
                    end=utils.get_default_end(),
                    api_param_mods={},
                    download_threads=None,
                    parse_threads=None,
                    IPV4=True,
                    IPV6=False,
                    bgpscanner=True):
        """Downloads and parses files using multiprocessing.

        In depth explanation at the top of the file.
            Start is epoch time which defaults to one week ago
            End is epoch time which defaults to six days ago
            Note: The reason start and end are earlier than a day ago is
                  to allow for the updated MRT files to get posted
            api_params defaults to None, later changed in _get_mrt_urls
            download_threads defaults to None, and later defaults to
                four times cpu_count
            parse_threads defaults to None, and later to cpu_count - 1
            IPV4 defaults to True, so IPV4 results are included
            IPV6 defaults to False, so IP6 results are not included
        """

        # Gets urls of all mrt files needed
        urls = self._get_mrt_urls(start, end, api_param_mods)
        self.logger.debug("Total files {}".format(len(urls)))
        # Get downloaded instances of mrt files using multithreading
        mrt_files = self._multiprocess_download(download_threads, urls)
        # Parses files using multiprocessing in descending order by size
        self._multiprocess_parse_dls(parse_threads, mrt_files, bgpscanner)
        self._filter_and_clean_up_db(IPV4, IPV6)

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_mrt_urls(self, start, end, PARAMS_modification={}):
        """Gets urls to download MRT files. Start and end should be epoch."""

        # Parameters for the get request, look at caida for more in depth info
        # This must be included in every API query
        PARAMS = {'human': True,
                  'intervals': ["{},{}".format(start, end)],
                  'types': ['ribs']
                  }
        # Other api calls can be made with these modifications
        PARAMS.update(PARAMS_modification)
        # API docs: https://bgpstream.caida.org/docs/api/broker#data
        # URL to make the api call to
        URL = 'https://bgpstream.caida.org/broker/data'
        # Request for data and conversion to json
        self.logger.debug(requests.get(url=URL, params=PARAMS).url)
        data = requests.get(url=URL, params=PARAMS).json()
        # Returns the urls from the json
        return [x.get('url') for x in data.get('data').get('dumpFiles')]

    @error_catcher()
    def _multiprocess_download(self, dl_threads, urls):
        """Downloads MRT files in parallel.

        In depth explanation at the top of the file, dl=download.
        """

        # Creates an mrt file for each url
        mrt_files = [MRT_File(self.path,
                              self.csv_dir,
                              url,
                              i + 1,
                              len(urls),
                              self.logger)
                     for i, url in enumerate(urls)]

        # Creates a dl pool with 4xCPUs since it is I/O based
        with utils.Pool(self.logger, dl_threads, 4, "download") as dl_pool:
            self.logger.debug("About to start downloading files")
            # Download files in parallel
            dl_pool.map(lambda f: utils.download_file(f.logger, f.url,
                        f.path, f.num, f.total_files, f.num/5), mrt_files)
            self.logger.debug("started to download files")
        return mrt_files

    @error_catcher()
    def _multiprocess_parse_dls(self, p_threads, mrt_files, bgpscanner):
        """Multiprocessingly(ooh cool verb, too bad it's not real)parse files.

        In depth explanation at the top of the file.
        dl=download, p=parse.
        """

        # Creates a parsing pool with cpu_count since it is CPU bound
        with utils.Pool(self.logger, p_threads, 1, "parsing") as p_pool:
            # Runs the parsing of files in parallel, largest first
            p_pool.map(lambda f: f.parse_file(bgpscanner),
                       sorted(mrt_files, reverse=True))

    @error_catcher()
    def _filter_and_clean_up_db(self, IPV4, IPV6):
        """This function filters mrt data by IPV family and cleans up db

        First the database is connected. Then IPV4 and/or IPV6 data is
        removed. Aftwards the data is vaccuumed and analyzed to get
        statistics for the table for future queries, and a checkpoint is
        called so as not to lose RAM.
        """

        with db_connection(MRT_Announcements_Table, self.logger) as ann_table:
            # First we filter by IPV4 and IPV6:
            ann_table.filter_by_IPV_family(IPV4, IPV6)
            # VACUUM ANALYZE to clean up data and create statistics on table
            # This is needed for better index creation and queries later on
            ann_table.cursor.execute("VACUUM ANALYZE;")
            # A checkpoint is run here so that RAM isn't lost
            ann_table.cursor.execute("CHECKPOINT;")
