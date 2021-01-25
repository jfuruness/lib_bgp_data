#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains class BGPStream_Website_Parser

The purpose of this class is to parse the information for BGP hijacks,
leaks, and outages from bgpstream.com. This information is then stored
in the database. This is done through a series of steps.

1. Initialize the three different kinds of data classes.
    -Handled in the __init__ function in BGPStream_Website_Parser
    -This class mainly deals with accessing the website, the data
     classes deal with parsing the information. These data classes
     inherit from the parent class Data
2. All rows are received from the main page of the website
    -This is handled in the utils.get_tags function
    -This has some initial data for all bgp events
3. The last ten rows on the website are removed
    -This is handled in the parse function in BGPStream_Website_Parser
    -There is some html errors there, which causes errors when parsing
4. The row limit is set so that it is not too high
    -This is handled in the parse function in BGPStream_Website_Parser
    -This is to prevent going over the maximum number of rows on website
5. Rows are iterated over until row_limit is reached
    -This is handled in the parse function
6. For each row, if that row is of a datatype passed in the parameters,
   and the row is new (by default) add that to the self.data dictionary
    -This causes that row to be parsed as well
    -Rows are parsed into CSVs and inserted into the database
7. Call the db_insert funtion on each of the data classes in self.data
    -This will parse all rows and insert them into the database
    -This formats the tables as well
        -Unwanted IPV4 or IPV6 prefixes are removed
        -Indexes are created if they don't exist
        -Duplicates are deleted
        -Temporary tables that are subsets of the data are created

Design Choices (summarizing from above):
    -The last ten rows of the website are not parsed due to html errors
    -Only the data types that are passed in as a parameter are parsed
        -This is because querying each individual events page for info
         takes a long time
        -Only new rows by default are parsed for the same reason
    -Multithreading isn't used because the website blocks the requests
    -Parsing is done from the end of the page to the top
        -The start of the page is not always the same

Possible Future Extensions:
    -Add test cases
    -Request of make bgpstream.com an api for faster request time?
        -It would cause less querying to their site
    -Multithread the first hundred results?
        -If we only parse new info this is the common case
"""

from .bgpstream_website_parser import BGPStream_Website_Parser
from .event_types import BGPStream_Website_Event_Types

__author__ = "Justin Furuness, Tony Zheng"
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
