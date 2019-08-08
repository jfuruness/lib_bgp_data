#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains RPKI Validator functionality

The purpose of this class is to obtain the validity data for all of the
prefix origin pairs in our announcements data, and insert it into a
database. This is done through a series of steps.

1. Write the validator file.
    -Handled in the _write_validator_file function
    -Normally the RPKI Validator pulls all prefix origin pairs from the
     internet, but those will not match old datasets
    -Instead, our own validator file is written
    -This file contains a placeholder of 100
        -The RPKI Validator does not observe anything seen by 5 or less
         peers
2. Host validator file
    -Handled in _serve_file decorator
    -Again, this is a file of all prefix origin pairs from our MRT
     announcements table
3. Run the RPKI Validator
    -Handled in run_validator function
4. Wait for the RPKI Validator to load the whole file
    -Handled in the _wait_for_validator_load function
    -This usually takes about 10 minutes
5. Get the json for the prefix origin pairs and their validity
    -Handled in the _get_ripe_data function
    -Need to query IPV6 port because that's what it runs on
6. Convert all strings to int's
    -Handled in the format_asn function
    -Done to save space and time when joining with later tables
7. Parsed information is stored in csv files, and old files are deleted
    -CSVs are chosen over binaries even though they are slightly slower
        -CSVs are more portable and don't rely on postgres versions
        -Binary file insertion relies on specific postgres instance
    -Old files are deleted to free up space
8. CSV files are inserted into postgres using COPY, and then deleted
    -COPY is used for speedy bulk insertions
    -Files are deleted to save space

Design choices (summarizing from above):
    -Indexes are not created because they are not ever used
    -We serve our own file for the RPKI Validator to be able to use
     old prefix origin pairs
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files

Possible Future Extensions:
    -Move the file serving functions into their own class
        -Improves readability?
    -Add test cases
    -Reduce total information in the headers
"""

from .rpki_validator import RPKI_Validator

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

