#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Caida_AS_Relationships_Parser

Caida_AS_Relationships_Parser first downloads all files from caida website
Then it unzips all these files
Then is parses all these files for their as_relationships
Then it deletes all the files that it downloaded
"""

import re
import requests
import bs4
import urllib.request
import shutil
import os
import bz2


class Caida_AS_Relationships_Parser:
    """This class downloads, unzips, parses, and deletes files from Caida"""

    def __init__(self, logger, args):
        """Initializes urls, regexes, and path variables"""

        # Path to where all files willi go. It does not have to exist
        if args.get("path") is None:
            self.path = "/tmp/bgp"
        self.unzipped_path = os.path.join(self.path + "unzipped")
        # URLs fom the caida websites to pull data from
        url_1 = 'http://data.caida.org/datasets/as-relationships/serial-1/'
        url_2 = 'http://data.caida.org/datasets/as-relationships/serial-2/'
        self.urls = [url_1, url_2]
        # Parse based on ^|, space, or newline
        self.divisor = re.compile(r'([^|\n\s]+)')
        self.logger = logger

    def download_files(self):
        """Downloads all .bz2 files from caida websites into self.path"""

        try:
            # Delete any files that are already in there
            self.clean_up()
            # Create directory if it does not exist
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            element_lists = []
            for url in self.urls:
                # Get all html tags that might have links
                element_lists.append([x for x in self._get_tags(url, 'a')])
            # Get total files
            total_files = file_counter = 0
            for element_list in elements_lists:
                total_files += len(element_list)

            for elements in element_lists:
                for element in elements:
                    # Only look at links with bz2 files
                    if "bz2" in element["href"]:
                        self._download_file(url, element["href"])
                        self.logger.info("{} / {} downloaded".format(
                            file_couner + 1, total_files))
                        file_counter += 1
        except Exception as e:
            self.logger.critical(
                "Problem downloading caida as_relationship files: {}"\
                    .format(e))
            raise e

    def unzip_files(self):
        """Unzips all .bz2 files in self.path into self.path_unzipped"""

        try:
            # Create the path if ut doesn't exist
            if not os.path.exists(self.unzipped_path):
                os.mkdir(self.unzipped_path)
            files = self._get_file_names(self.path)
            # We do this so we don've to call len every iteration
            len_files = len(files)
            for i in range(len_files):
                # Unzips .bz2 into a new file
                self._unzip_file(files[i])
                self.logger.info("{} / {} unzipped".format(i + 1, len_files))
        except Exception as e:
            self.logger.critical(
                "Problem unzipping caida as_relationship files: {}"\
                    .format(e))
            raise e


    def parse_files(self):
        """Returns a list of dicts of info from as_relationship files

        There are three different formats of files that are downloaded.
        Each helper function retrieves data from a different file format
        """
        try:
            data = []
            files_names = self._get_file_names(self.unzipped_path)
            # We do this so we don't have to call len for every iteration
            len_file_names = len(file_names)

            # for all files in self.path_unzipped
            for i in range(file_names):

                # Open file for read only
                temp_file = open(
                                os.path.join(self.unzipped_path, file_names[i]), "r")
                lines = temp_file.readlines()

                # Parse non comment lines depending on file format
                if "ppdc" in file_names[i]:
                    temp = [self._parse_ppdc(x) for x in lines if "#" not in x]
                elif "as-rel.txt" in file_names[i]:
                    temp = [self._parse_as(x) for x in lines if "#" not in x]
                elif "as-rel2.txt" in file_names[i]:
                    temp = [self._parse_as2(x) for x in lines if "#" not in x]
                data.extend(temp)
    
                temp_file.close()
                self.logger.info("Parsed {}/{} files".format(i + 1, len_files))
            return data
        except Exception as e:
            self.logger.critical(
                "Problem parsing caida as_relationship files: {}"\
                    .format(e))
            raise e

    def clean_up(self):
        """Permanently deletes all the files in paths specified"""

        try:
            if os.path.exists(self.path):
                # rm -rf self.path
                shutil.rmtree(self.path)
            if os.path.exists(self.unzipped_path):
                # rm -rf self.unzipped_path
                shutil.rmtree(self.unzipped_path)
            self.logger.info("Deleted all caida as_relationship files")
        except Exception as e:
            self.logger.critical(
                "Problem cleaning up caida as_relationship files: {}"\
                    .format(e))
            raise e

#######################################
### download_files Helper Functions ###
#######################################

    def _get_tags(self, url, tag):
        """Gets the html of a given url, and returns a list of tags"""

        response = requests.get(url)
        # Raises an exception if there was an error
        response.raise_for_status()
        # Creates a beautiful soup object from the get request
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        # Create a list of tags from the html and return them
        return [x for x in soup.select(tag)]

    def _download_file(self, url, link):
        """Downloads a file from a link"""

        # os.path.join is neccessary for cross platform compatability
        path = os.path.join(self.path, link)
        with urllib.request.urlopen(url + link)\
                as response, open(path, 'wb') as out_file:
            # Copy the file into the specified file_path
            shutil.copyfileobj(response, out_file)

####################################
### unzip_files Helper Functions ###
####################################

    def _unzip_file(self, file_name):
        """Unzips bz2 file into a new file"""

        # Get path names
        path = os.path.join(self.path, file_name)
        new_path = os.path.join(self.unzipped_path,
                                file_name[:-4] + '.decompressed')
        # Unzip and write to new file
        with open(new_path, 'wb') as new_file,\
                bz2.BZ2File(path, 'rb') as file:
            for data in iter(lambda: file.read(100 * 1024), b''):
                new_file.write(data)

####################################
### parse_files Helper Functions ###
####################################

    def _parse_ppdc(self, line):
        """Parses ppdc file line for data and outputs a dict

        Format of a ppdc file: <cone_as> <customer_as_1>...<customer_as_n>
        """

        # Gets a list of numbers
        nums = self.divisor.findall(line)
        return {"cone_as": nums[0], "customer_as": nums[1:]}

    def _parse_as(self, line):
        """Parses as_rel file line for data and outputs a dict

        Format of a as_rel file:
        <provider_as> | <customer_as> | -1
        <peer_as> | <peer_as> | 0
        """
        nums = self.divisor.findall(line)
        classifier = nums[2]
        if classifier == '-1':
            return {"provider_as": nums[0], "customer_as": nums[1]}
        elif classifier == '0':
            return {"peer_as_1": nums[0], "peer_as_2": nums[1]}
        else:
            raise Exception("classifier unknown: {}".format(classifier))

    def _parse_as2(self, line):
        """Parses as_rel files for data and outputs a dict

        Format of a as_rel file:
        <provider_as> | <customer_as> | -1
        <peer_as> | <peer_as> | 0 | <source>
        """

        groups = self.divisor.findall(line)
        classifier = groups[2]
        if classifier == '-1':
            return {"provider_as": groups[0], "customer_as": groups[1]}
        elif classifier == '0':
            return {"peer_as_1": groups[0],
                    "peer_as_2": groups[1],
                    "source": groups[3]}
        else:
            raise Exception("classifier unknown: {}".format(classifier))

##############################
### Other Helper Functions ###
##############################

    def _get_file_names(self, path):
        """Returns a list of file names within a given path"""

        for (_, _, files) in os.walk(path):
            return files
