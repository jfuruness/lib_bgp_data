#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Parser

The purpose of this class is to download the mrt files and insert them
into a database. This is done through a series of steps.

Read README for in depth explanation.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import datetime
import requests
import warnings
from .mrt_file import MRT_File
from .mrt_sources import MRT_Sources
from .tables import MRT_Announcements_Table
from ..base_parser import Parser
from ..utils import utils, db_connection
from ..utils.utils import progress_bar

class MRT_Parser(Parser):
    """This class downloads, parses, and deletes files from Caida.

    In depth explanation at the top of module.
    """

    __slots__ = []

    def __init__(self, *args, **kwargs):
        """Initializes logger and path variables."""

        if len(args) > 0 and isinstance(args[0], dict):
            warnings.warn(("Passing in a dict for args is depreciated\n"
                           "\tPlease pass in using keyword arguments"),
                          DeprecationWarning,
                          stacklevel=1)
            kwargs = args[0]
        super(MRT_Parser, self).__init__(**kwargs)
        with db_connection(MRT_Announcements_Table, self.logger) as _ann_table:
            # Clears the table for insertion
            _ann_table.clear_tables()
            # Tables can't be created in multithreading so it's done now
            _ann_table._create_tables()

    def _run(self,
             *args,
             start=utils.get_default_start(),
             end=utils.get_default_end(),
             api_param_mods={},
             download_threads=None,
             parse_threads=None,
             IPV4=True,
             IPV6=False,
             bgpscanner=True,
             sources=MRT_Sources.__members__.values()):
        """Downloads and parses files using multiprocessing.

        In depth explanation in README.
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
        urls = self._get_mrt_urls(start, end, api_param_mods, sources)
        self.logger.debug(f"Total files {len(urls)}")
        # Get downloaded instances of mrt files using multithreading
        mrt_files = self._multiprocess_download(download_threads, urls)
        # Parses files using multiprocessing in descending order by size
        self._multiprocess_parse_dls(parse_threads, mrt_files, bgpscanner)
        self._filter_and_clean_up_db(IPV4, IPV6)

########################
### Helper Functions ###
########################

    def _get_mrt_urls(self,
                      start: int,
                      end: int,
                      PARAMS_modification={},
                      sources=[]):
        """Gets caida and iso URLs, start and end should be epoch"""

        self.logger.info(f"Getting MRT urls for {[x.name for x in sources]}")
        caida_urls = self._get_caida_mrt_urls(start,
                                              end,
                                              sources,
                                              PARAMS_modification)
        # Give Isolario URLs if parameter is not changed
        return caida_urls + self._get_iso_mrt_urls(start, sources) 
        # If you ever want RIPE without the caida api, look at the commit
        # Where the relationship_parser_tests where merged in

    def _get_caida_mrt_urls(self,
                            start: int,
                            end: int,
                            sources: list,
                            PARAMS_modification={}) -> list:
        """Gets urls to download MRT files. Start and end should be epoch."""

        # Parameters for the get request, look at caida for more in depth info
        # This must be included in every API query
        PARAMS = {'human': True,
                  'intervals': ["{},{}".format(start, end)],
                  'types': ['ribs']
                  }
        # Done this way because cannot specify two params with same name
        if MRT_Sources.RIPE in sources and MRT_Sources.ROUTE_VIEWS in sources:
            pass
        # Else just routeviews:
        elif MRT_Sources.RIPE in sources:
            PARAMS["projects[]"] = ["ris"]
        # else just ripe
        elif MRT_Sources.ROUTE_VIEWS in sources:
            PARAMS["projects[]"] = ["routeviews"]
        # else neither
        else:
            return []
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

    def _get_iso_mrt_urls(self, start: int, sources: list) -> list:
        """Gets URLs to download MRT files from Isolario.io

        Start should be in epoch"""

        if MRT_Sources.ISOLARIO not in sources:
            self.logger.debug("Not getting isolario urls")
            return []

        # API URL
        _url = "http://isolario.it/Isolario_MRT_data/"
        # Get the collectors from the page
        # Slice out the parent directory link and sorting links
        _collectors = [x["href"] for x in utils.get_tags(_url, 'a')[0]][5:]
        _start = datetime.datetime.fromtimestamp(start)

        # Get the folder name according to the start parameter
        _folder = _start.strftime("%Y_%m/")
        # Isolario files are added every 2 hrs, so if start time is odd numbered,
        # then make it an even number and add an hour
        # https://stackoverflow.com/q/12400256/8903959
        if _start.hour % 2 != 0:
            _start.replace(hour=_start.hour + 1)

        # The file name for the RIB wanted according to the start parameter...
        _start_file = f'rib.{_start.strftime("%Y%m%d.%H00")}.bz2'

        # Make a list of all possible file URLs
        return [_url + _coll + _folder + _start_file for _coll in _collectors]

    def _multiprocess_download(self, dl_threads: int, urls: list) -> list:
        """Downloads MRT files in parallel.

        In depth explanation at the top of the file, dl=download.
        """

        # Creates an mrt file for each url
        mrt_files = [MRT_File(self.path,
                              self.csv_dir,
                              url,
                              i + 1,
                              self.logger)
                     for i, url in enumerate(urls)]

        with progress_bar(self.logger, "Downloading MRTs, ", len(mrt_files)):
            # Creates a dl pool with 4xCPUs since it is I/O based
            with utils.Pool(self.logger, dl_threads, 4, "download") as dl_pool:
                
                # Download files in parallel
                dl_pool.map(lambda f: utils.download_file(
                        f.logger, f.url, f.path, f.num, len(urls),
                        f.num/5, progress_bar=True), mrt_files)
        return mrt_files

    def _multiprocess_parse_dls(self,
                                p_threads: int,
                                mrt_files: list,
                                bgpscanner: bool):
        """Multiprocessingly(ooh cool verb, too bad it's not real)parse files.

        In depth explanation at the top of the file.
        dl=download, p=parse.
        """


        with progress_bar(self.logger, "Parsing MRT Files,", len(mrt_files)):
            with utils.Pool(self.logger, p_threads, 1, "parsing") as p_pool:
                # Runs the parsing of files in parallel, largest first
                p_pool.map(lambda f: f.parse_file(bgpscanner),
                           sorted(mrt_files, reverse=True))

    def _filter_and_clean_up_db(self, IPV4: bool, IPV6: bool):
        """This function filters mrt data by IPV family and cleans up db

        First the database is connected. Then IPV4 and/or IPV6 data is
        removed. Aftwards the data is vaccuumed and analyzed to get
        statistics for the table for future queries, and a checkpoint is
        called so as not to lose RAM.
        """

        with db_connection(MRT_Announcements_Table, self.logger) as _ann_table:
            # First we filter by IPV4 and IPV6:
            _ann_table.filter_by_IPV_family(IPV4, IPV6)
            # VACUUM ANALYZE to clean up data and create statistics on table
            # This is needed for better index creation and queries later on
            _ann_table.cursor.execute("VACUUM ANALYZE;")
            # A checkpoint is run here so that RAM isn't lost
            _ann_table.cursor.execute("CHECKPOINT;")

    def parse_files(self, **kwargs):
        warnings.warn(("MRT_Parser.parse_files is depreciated. "
                       "Use MRT_Parser.run instead"),
                      DeprecationWarning,
                      stacklevel=1)
        self._run(self, **kwargs)
