#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This submodule contains a relationship parser

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
2. Then the Relationships_File class is then instantiated
3. The relationship file is then downloaded
    -This is handled in the utils.download_file function
4. Then the file is unzipped
    -handled by utils _unzip_bz2
5. The relationship file is then split into two
    -Handled in the Relationships_File class
    -This is done because the file contains both peers and
     customer_provider data.
    -The file itself is a formatted CSV with "|" delimiters
    -Using grep and cut the relationships file is split and formatted
    -This is done instead of regex because it is faster and simpler
6. Then each CSV is inserted into the database
    -The old table gets destroyed first
    -This is handleded in the utils.csv_to_db function
    -This is done because the file comes in CSV format
    -Optionally data can be inserted into ROVPP tables
7. The config is updated with the last date a file was parsed

Design Choices:
    -CSV insertion is done because the relationships file is a CSV
    -Dates are stored and checked to prevent redoing old work
    -An enum was used to make the code cleaner in relationship_file
        -Classes are more messy in this case


Possible Future Extensions:
    -Add test cases
    -Possibly take out date checking for cleaner code?
     Saves very little time
    -Move unzip_bz2 to this file? Nothing else uses it anymore
    -Possibly change the name of the table to provider_customers
        -That is the order the data is in, it is like that in all files
"""

from .relationships_parser import Relationships_Parser

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
