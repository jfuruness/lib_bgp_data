#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ROAs Collector to download/store ROAs from rpki
"""

import requests
import shutil
import os
import datetime
from datetime import timedelta
import urllib
import json
import re
import csv
from ..logger import Logger, error_catcher
from .tables import ROAs_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROAs_Collector:
    """This class downloads, and stores ROAs from rpki validator""" 

    __slots__ = ['path', 'csv_directory', 'args', 'url', 'logger',
                 'start_time', 'csv_name', 'test']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Path to where all files willi go. It does not have to exist
        self.path = args.get("path")
        if self.path is None:
            self.path = "/tmp/bgp_mrt"
        self.csv_directory = args.get("csv_directory")
        if self.csv_directory is None:
            self.csv_directory = "/dev/shm/bgp_roas"
        self.args = args
        # URLs fom the caida websites to pull data from
        self.url = 'https://rpki-validator.ripe.net/api/export.json'
        self.logger = Logger(args).logger
        self.test = False
        self.logger.info("Initialized ROAs Collector at {}".format(
            datetime.datetime.now()))

    @error_catcher()
    def parse_roas(self, db=True):
        """Downloads and stores roas from a json"""

        self.start_time = datetime.datetime.now()
        # Gets rid of any files already there
        self._clean_path()
        try:
            self._write_csv(self._get_roas())
            self._bulk_insert_db() 
        except Exception as e:
            self.logger.error(e)
            raise (e)
        finally:
            # Clean up don't be messy yo
            self._end_parser()

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_roas(self):
        """Returns all the roas from the rpki validator"""

        return self._format_roas(self._get_json_roas())

    @error_catcher()
    def _get_json_roas(self):
        """Returns the json from the url for the roas"""

        # Need these headers so that the xml can be accepted
        headers = {"Accept":"application/xml;q=0.9,*/*;q=0.8"}
        # Formats request
        req = urllib.request.Request(self.url, headers=headers)
        # opens request
        with urllib.request.urlopen(req) as url:
            # Gets data from the json in the url
            return json.loads(url.read().decode())["roas"]

    @error_catcher()
    def _format_roas(self, unformatted_roas):
        """Format the roas to be input to a csv"""

        # I know you can use a list comp here but it's messy
        # Formats roas for csv
        formatted_roas = []
        for roa in unformatted_roas:
            formatted_roas.append(
                [int(re.findall('\d+', roa["asn"])[0]),  # Gets ASN
                 roa["prefix"],
                 int(roa["maxLength"])
                 ]) 
        return formatted_roas

    @error_catcher()
    def _write_csv(self, roas):
        """Writes all csvs to a file to be inputted to a db"""

        self.csv_name = "{}/roas.csv".format(self.csv_directory)
        self.logger.info("Writing to {}".format(self.csv_name))
        with open(self.csv_name, mode='w') as temp_csv:
            csv_writer = csv.writer(temp_csv,
                                    delimiter='\t',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
            # Writes all the information to a csv file
            # Writing to a csv then copying into the db
            # is the fastest way to insert files
            csv_writer.writerows(roas)

    @error_catcher()
    def _bulk_insert_db(self):
        """Inserts a csv file to the database"""

        self.logger.info("Copying {} into the database".format(self.csv_name))
        db = ROAs_Table(self.logger, test=self.test)
        db.clear_table()
        # Opens temporary file
        f = open(r'{}'.format(self.csv_name), 'r')

        # Copies data from the csv to the db, this is the fastest way

        # NOTE: servers are down so I can't test, but I don't think
        # that the mrt_announcements is supposed to have quotes
        db.cursor.copy_from(f,
                            db.table,
                            sep='\t',
                            columns=db.columns)

        test_data = None

        # Closes file
        f.close()
        # Closes db connection
        db.close()
        self.logger.info("Done inserting {} into the database".format(
            self.csv_name))
        return test_data


    @error_catcher()
    def _clean_path(self, end=False):
        """If path exists, remove it. Create it and change permissions"""

        for path in [self.path, self.csv_directory]:
            if os.path.exists(path):
                shutil.rmtree(path)
            if not end:
                os.makedirs(path)
                # This is just for testing, it doesn't work on the server
                os.chmod(path, 0o777)

    @error_catcher()
    def _end_parser(self):
        """Cleans up after the parser"""

        # Deletes everything at the end no matter what happens
        self._clean_path(end=True)
        self.logger.info("Parser completed at {}".format(
            datetime.datetime.now()))
        self.logger.info("Parser started at {}".format(self.start_time))
