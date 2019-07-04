#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROAs Collector

The purpose of this class is to download ROAs from rpki and insert them
into a database. This is done through a series of steps.

1. Clear the Roas table
    -Handled in the parse_roas function
2. Make an API call to https://rpki-validator.ripe.net/api/export.json
    -Handled in the _get_json_roas function
    -This will get the json for the roas
3. Format the roa data for database insertion
    -Handled in the _format_roas function
4. Insert the data into the database
    -Handled in the utils.rows_to_db
    -First converts data to a csv then inserts it into the database
    -CSVs are used for fast bulk database insertion
5. An index is created on the roa prefix
    -The purpose of this is to make the SQL query faster when joining
     with the mrt announcements

Design Choices (summarizing from above):
    -CSVs are used for fast database bulk insertion
    -An index on the prefix is created on the roas for fast SQL joins

Possible Future Extensions:
    -Add test cases
"""

from .roas_collector import ROAs_Collector

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
