#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Detailed.

The purpose of this class is to extend mrt_parser and ensure that all
ribs and updates over a interval are obtained, as opposed to just the
oldest dump of an interval. It also has options to get updates, 
as opposed to just getting rib dumps.
"""

__authors__ = ["Nicholas Shpetner"]
__credits__ = ["Nicholas Shpetner"]
__License__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import datetime
import logging
import os
import warnings
import requests
from .detailed_mrt_file import Detailed_MRT_File
from .mrt_installer import MRT_Installer
from .mrt_sources import MRT_Sources
from .mrt_types import MRT_Types
from .mrt_parser import MRT_Parser
from .detailed_tables import MRT_Detailed_Table
from ..base_classes import Parser
from ..utils import utils


class MRT_Detailed(MRT_Parser):
    """This class downloads, parses, and deletes MRT files.
    It is an extension of MRT_Parser. See the readme for that class
    for further details.
    """
    __slots__ = []

    def __init__(self, **kwargs):
        """Initalizes logger and path variables"""
        super(MRT_Detailed, self).__init__(**kwargs)
        with MRT_Detailed_Table() as _ann_table:
            # Resets the table:
            _ann_table.clear_table()
            _ann_table._create_tables()
        if not os.path.exists("/usr/bin/bgpscanner"):
            logging.warning("Dependencies are being installed.")
            MRT_Installer.install_dependencies()

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
             sources=MRT_Sources.__members__.values(),
             mrt_types=MRT_Types,
             detailed=True):
             # TODO: Make typ enum, make param list of enums to get
             # Time fields in new table: interval_start, interval_end
             # might need to make new updates mrt_file in order to parse update info and get 
             # update type
             # Add param to determine whether or not to get detailed info
             # continue to add tests if necessary.
             # After this: get another meeting w/ justin. 
        """Downloads and parses files by extending MRT_Parser.
        This parser will get updates in addition to rib dumps,
        and will split the given interval into sub intervals to get
        all dumps. For each dump, it will store the type of the dump
        and the interval it was located in.
        If detailed is set to true, the detailed MRT parser will check
        MRT_Types for sources, types, and rate (i.e. the time the type
        of a source takes for the next dump). It will NOT use
        MRT_Sources. However, if detailed is set to false, MRT_Sources
        will be used and all args will be passed to MRT_Parser. 
        When detailed is set to true, all results will be stored in
        MRT_Detailed_Table, however if detailed is set to false results
        will be stored in the original MRT_Announcements_Table
        For further information, see the documentation in MRT_Parser
        and the README.
        """

        # Warning about Caida
        logging.warning(("Caida api doesn't work as you'd expect."
                         " There are bugs. To ensure a good run, epoch"
                         " times must start 5 seconds before day, and"
                         " end 1 second before end of the day"))
        urls = []
        if detailed:
            # If detailed = true, run through this detailed parser
            # Isolario not included as apparently it's too slow.
            urls = self._get_caida_mrt_urls(mrt_types,
                                            start,
                                            end,
                                            api_param_mods)
            logging.debug(f"Total files {len(urls)}")
            mrt_files = self._multiprocess_download(download_threads,
                                                    urls)
            self._multiprocess_parse_dls(parse_threads,
                                         mrt_files,
                                         bgpscanner)
            self._filter_and_clean_up_db(IPV4, IPV6)
        else:
            # Else, run through the original parser with given args.
            logging.warning(("Now using MRT_Parser."
                             "Results go in mrt announcements table"))
            super()._run(*args,
                         start=utils.get_default_start(),
                         end=utils.get_default_end(),
                         api_param_mods={},
                         download_threads=None,
                         parse_threads=None,
                         IPV4=True,
                         IPV6=False,
                         bgpscanner=True,
                         sources=MRT_Sources.__members__.values())


#######################
### Helper Functions###
#######################

    def _get_subintervals(self,
                          start_time: int,
                          end_time: int,
                          rate: int) -> list:
        """Takes a time interval and splits it into subintervals based
        on the rate of new dumps, in seconds.
        The resulting subinterval starts and ends with the original
        interval, with each interval the size of rate. However, since
        it is unlikley the original interval can be evenly divided by
        rate, the function will cut down the last subinterval to fit it
        in the original interval.
        e.g, for a interval of 10 seconds with a 3 second rate, you'd
        have 3 three second intervals and 1 one second interval
        """
        times = []
        diff = end_time - start_time
        intervals = int(diff / rate)
        # Leftover is used to calculate the size of the last interval.
        # There's a better way to do this, but I'll work on it later.
        leftover = float(diff / rate) % 1
        for i in range(intervals):
            times.append((end_time - rate, end_time))
            end_time += rate
        end_time -= rate
        times.append((end_time, end_time + (rate * leftover)))
        return times

    def _get_caida_mrt_urls(self,
                            mrt_types,
                            start: int,
                            end: int,
                            PARAMS_modification={}) -> list:
        """Like the original function, gets the urls of various dumps
        from Caida. However, as mentioned above, it does not use
        MRT_Sources, but rather MRT_Types to get source, type, and
        rate.
        """
        PARAMS = {'human': True}
        URL = 'https://bgpstream.caida.org/broker/data'
        urls = []
        # Now we run through MRT_Types.
        for source in mrt_types:
            # Name of project, either routeviews or ris usually.
            PARAMS["projects[]"] = [str(source.value[0])]
            for typ in source.value[1]:
                # Type of the dump, either ribs or updates usually.
                PARAMS['type'] = typ
                times = self._get_subintervals(start,
                                               end,
                                               source.value[1][typ])
                for time in times:
                    # Iterate through the list of subintervals, get our
                    # data.
                    PARAMS['intervals'] = [f"{time[0]}, {time[1]}"]
                    PARAMS.update(PARAMS_modification)
                    logging.debug(requests.get(url=URL, params=PARAMS).url)
                    data = requests.get(url=URL, params=PARAMS).json()
                    urls = urls + ([[x.get('url'), time[0], time[1]] for x in data.get('data').get('dumpFiles')])
        return urls

    def _multiprocess_download(self, 
                               dl_threads: int, 
                               urls: list) -> list:
        """Extends MRT_Parser._multiprocess_download by giving
        Detailed_MRT_File not only the URL but also the interval of the
        file, i.e. the subinterval we got the file.
        """
        mrt_files = [Detailed_MRT_File(self.path, 
                                       self.csv_dir, 
                                       url[0],
                                       url[1],
                                       url[2], 
                                       i+1) for i, url in enumerate(urls)]
        # After the above, standard fare.
        with utils.progress_bar("Downloading detailed MRTs, ", len(mrt_files)):
            # Creates a dl pool with 4xCPUs since it is I/O based
            with utils.Pool(dl_threads, 4, "download") as dl_pool:
                dl_pool.map(lambda f: utils.download_file(
                            f.url, f.path, f.num, len(urls),
                            f.num/5, progress_bar=True), mrt_files)
        return mrt_files

    def _multiprocess_parse_dls(self,
                                p_threads: int,
                                mrt_files: list,
                                bgpscanner: bool):
        with utils.progress_bar("Parsing detailed MRT files", len(mrt_files)):
            with utils.Pool(p_threads, 1, "parsing") as p_pool:
                p_pool.map(lambda f: f.parse_file(bgpscanner), 
                           sorted(mrt_files, reverse=True))

    def _filter_and_clear_up_db(self, IPV4: bool, IPV6: bool):
        with MRT_Detailed_Table() as _mrt_table:
            _mrt_table.filter_by_IPV_family(IPV4, IPV6)
            _mrt_table.cursor.execute("VACUUM ANALYZE;")
            _mrt_table.cursor.execute("CHECKPOINT;")
