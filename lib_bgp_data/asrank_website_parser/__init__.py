#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains class ASRankWebsiteParser.

The purpose of this class is to parse the information of various AS's
from asrank.caida.org. This information is then stored
in the database. This is done through a series of steps.

1. Initialize the ASRankData classes that will store the data
    -Handled in the __init__ function
    -This class mainly deals with inserting the data into lists
     and then eventually into the database
2. All rows/pages are recieved from the main page of the website
    -This is handled within the _run_parser method
    -The _run_parser method uses get_page method within SelDriver class
3. The data is parsed within the ASRankData class
    -The insert_data method is used to insert all the rows from a page
    -The insert_data method parses the HTML
4. Rows and pages are iterated over until all the rows are parsed
    -The threads split up the pages so that there is no interference
     from other threads
5. Call the insert_data_into_db method within the ASRankData class
    -The data is converted into a csv file before inserting
    -This will parse all rows and insert them into the database
    -This formats the tables as well
        -Indexes are created if they don't exist

Design Choices (summarizing from above):
    -Only the five attribute table found on the front of website is parsed
    -Parsing is done from the top of the first page to the end of last page
    -Multithreading is used because the task is less computationally intensive
     than IO intensive

Possible Future Extensions:
    -Add test cases
"""
from .asrank_website_parser import ASRankWebsiteParser

__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"
