#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class parser that can parse bgp data"""

import multiprocessing
import logging
from .logger import Logger
from .announcements import BGP_Records
from .as_relationships import Caida_AS_Relationships_Parser
from .bgpstream import BGPStream_Website_Parser
from . import Database


class Parser(Logger):
    """Parses bgp data into a database

    parses data from bgpstream.com, caida as relationships,
    and caida announcements and inserts it into a database
    """

    def __init__(self,
                 database,
                 bgpstream_args={},
                 announcements_args={},
                 as_relationship_args={},
                 log_name="parser.log",
                 log_file_level=logging.ERROR,
                 log_stream_level=logging.INFO
                 ):
        """Initializes database and parsers"""

        # Function can be found in logger.Logger class
        # sets self.logger
        self._initialize_logger(log_name, log_file_level, log_stream_level)
        self.database = database
        self.bgpstream_parser = BGPStream_Website_Parser(self.logger,
                                                         bgpstream_args)
        self.announcements_parser = BGP_Records(self.logger,
                                                announcements_args)
        self.as_relationships_parser = Caida_AS_Relationships_Parser(
            self.logger, as_relationship_args)

    def run_bgpstream_parser(self, max_processes=multiprocessing.cpu_count()):
        """Parses bgpstream.com and inserts into the database"""

        try:
            self.logger.info("Running bgpstream website parser")
            events = self.bgpstream_parser.parse(max_processes)
            for event in events:
                if event.get("event_type") == 'BGP Leak':
                    self.database.add_leak_event(event)
                elif event.get("event_type") == 'Outage':
                    self.database.add_outage_event(event)
                elif event.get("event_type") == 'Possible Hijack':
                    self.database.add_hijack_event(event)
            self.logger.info("Done running bgpstream website parser")
        except Exception as e:
            self.logger.critical(
                "Problem running bgpstream parser: {}".format(e))
            raise e

    def run_as_relationship_parser(self, downloaded=False, clean_up=True):
        """Parses as relationships and inserts them into database"""

        try:
            self.logger.info("Running as relationship parser")
            if downloaded is False:
                self.as_relationships_parser.download_files()
                self.as_relationships_parser.unzip_files()
            lines = self.as_relationships_parser.parse_files()
            total_lines = len(lines)
            for i in range(total_lines):
                self.database.add_as_relationship(lines[i])
                self.logger.info(
                    "{}/{} relationships resolved".format(i, total_lines))
            if clean_up:
                self.as_relationships_parser.clean_up()
            self.logger.info("Done running as relationship parser")
        except Exception as e:
            self.logger.critical(
                "Problem running as_relationship_parser: {}".format(e))
            if clean_up:
                self.as_relationships_parser.clean_up()
            raise e


    def run_as_announcements_parser(self, start, end):
        """Parses bgp announcements and inserts them into the database"""

        try:
            # start = datetime.datetime(2015, 8, 1, 8, 20, 11)
            # end = start
            self.logger.info("Running as announcements parser")
            announcements = self.announcements_parser.get_records(start, end)
            for announcement in announcements:
                self.database.insert_announcement_info(announcement)
            self.logger.info("Done running as announcements parser")
        except Exception as e:
            self.logger.critical(
                "Problem running as_announcements_parser: {}".format(e))
            raise e

