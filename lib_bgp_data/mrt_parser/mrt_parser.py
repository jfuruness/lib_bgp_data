#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Caida_MRT_Parser
Caida_MRT_Parser first determines all of the urls from which to download mrt
files. Afterwards it goes one by one, downloading the mrt file, unzipping it,
parsing it, and deleting it. It can do this for any time period.
A note on how this works. The module downloads all files first, lists them by
size, then parses them. This is because if it is not done this way, then the
largest files get downloaded last, and end up running when all other processes
have finished, and isn't efficient. If you run it with overlap, meaning that
it starts parsing once the downloading is nearly done, the time extends
for many reasons. One of them being that more processes are running. The
second is that the largest files get downloaded last, but these should be
parsed first. The third is that to transfer information between processes, a
queue must be used, which is extremely slow, and the locking mechanism causes
a significant slowdown in the application. I've tested it both ways, and with
overlapping the download and parsing processes the time for inserting a days
worth of data increased by more than a half hour when I killed the program.
Also I've experimented with the number of parse and download processes. For
downloading, it is mostly IO based and so should have as many processes as
the system allows. The second should not have more processes than the system
has because it is not mostly io based (the only io is db insertion which is
quick and csv writing which is done in one step)
"""

import requests
import shutil
import os
import datetime
from datetime import timedelta
from multiprocessing import cpu_count
from pathos.multiprocessing import ProcessingPool
from contextlib import contextmanager
from .mrt_file import MRT_File
from .logger import Logger
from ..logger import error_catcher
from .tables import Announcements_Table
from .. import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

@contextmanager
def Pool(logger, threads, multiplier, name):
    """Context manager for pathos ProcessingPool"""

    # Creates a pool with threads else cpu_count * multiplier
    p = ProcessingPool(threads if threads else cpu_count() * multiplier)
    logger.info("Created {} pool".format(name))
    yield p
    (p.close(), p.join())


class MRT_Parser:
    """This class downloads, unzips, parses, and deletes files from Caida
    Deeper explanation at the top of module
    """

    __slots__ = ['path', 'csv_dir', 'args', 'url', 'logger', 'start_time',
                 'dl_pool', 'p_pool', 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args, "mrt")
        # URLs fom the caida websites to pull data from
        self.url = 'https://bgpstream.caida.org/broker/data'
        self.logger = Logger(args.get("stream_level"))
        table = Announcements_Table(self.logger)
        table.clear_table()
        table.close()

    @error_catcher()
    @utils.run_parser()
    def parse_files(self,
                    start=(utils.now()-timedelta(days=1)).timestamp(),
                    end=utils.now().timestamp(),
                    db=True,
                    download_threads=None,
                    parse_threads=None,
                    IPV4=True,
                    IPV6=False):
        """Downloads, unzips, and parses files using multiprocessing
        This Function downloads, unzips, and parses files one by one.
        Start and End are the epoch intervals for mrt files. Explanation at
        top of file. Other Design choices: We don't delete duplicates because
        there are so few and the query is unnessecarily long (~2% duplicates)
        """

        print("0000000000000000000000000")
        # Gets urls of all mrt files needed
        urls = self._get_mrt_urls(start, end)
        print("11111111111111")
        # Get downloaded instances of mrt files using multiprocessing
        mrt_files = self._multiprocess_download(download_threads, urls)
        print("@@@@@@@@@@@@@@@@@")
        # Parses files using multiprocessing in descending order by size
        self._multiprocess_parse_dls(parse_threads, mrt_files, IPV4, IPV6, db)
        table = Announcements_Table(self.logger)
        table.create_index()
        table.vacuum()
        table.close()
        

########################
### Helper Functions ###
########################

    def _multiprocess_download(self, dl_threads, urls):
        """Downloads files in parallel. Explanation at the top, dl=download"""

        mrt_files = [MRT_File(self.path,
                              self.csv_dir,
                              url,
                              i + 1,
                              len(urls),
                              Logger(self.args.get("stream_level")))
                     for i, url in enumerate(urls)]

        print("FFFF")
        # Creates a dl pool, I/O based, so get as many threads as possible
        with Pool(self.logger, dl_threads, 4, "download") as dl_pool:
            self.logger.debug("About to start downloading files")
            print("GGGG")
            dl_pool.map(lambda f : utils.download_file(f.logger, f.url, f.path,
                f.num, f.total_files, f.num/5), mrt_files)
            print("HHHH")
            self.logger.debug("started to download files")
        return mrt_files

    def _multiprocess_parse_dls(self, p_threads, mrt_files, IPV4, IPV6, db):
        """Multiprocessingly (ooh cool verb, to bad it's not real) parse files
        explanation at the top of the file. p=parse, dl=download
        """

        # Creates a parsing pool
        with Pool(self.logger, p_threads, 1, "parsing") as  p_pool:
            p_pool.map(lambda f, db, IPV4, IPV6: f.parse_file(db, IPV4, IPV6),
                       sorted(mrt_files, reverse=True),  #  Largest first
                       [db]*len(mrt_files),
                       [IPV4]*len(mrt_files),
                       [IPV6]*len(mrt_files))

    @error_catcher()
    def _get_mrt_urls(self, start, end):
        """Gets urls to download mrt files. Start and end should be epoch"""

        # Paramters for the get request, look at caida for more in depth info
        PARAMS = {'human': True,
                  'intervals': ["{},{}".format(start, end)],
                  'types': ['ribs']
                  }
        # Request for data and conversion to json
        data = requests.get(url=self.url, params=PARAMS).json()
        # Returns the urls
        return [x.get('url') for x in data.get('data').get('dumpFiles')]
