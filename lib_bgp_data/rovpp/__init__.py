#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This subpackage contains the functionality to parse MRT files.

The purpose of this subpackage is to download the mrt files and insert them
into a database. This is done through a series of steps.

1. Make an api call to https://bgpstream.caida.org/broker/data
    -Handled in _get_mrt_urls function
    -This will return json for rib files which contain BGP announcements
    -From this we parse out urls for the BGP dumps
    -This only returns the first dump for the time interval given
        -However, we only want one dump, multiple dumps would have
         data that conflicts with one another
        -For longer intervals use one BGP dump then updates
2. Then all the mrt files are downloaded in parallel
    -Handled in MRT_Parser class
    -This instantiates the MRT_File class with each url
        -utils.download_file handles downloading each particular file
    -Four times the CPUs is used for thread count since it is I/O bound
        -Mutlithreading with GIL lock is better than multiprocessing
         since this is just intesive I/O in this case
    -Downloaded first so that we parse the largest files first
    -In this way, more files are parsed in parallel (since the largest
     files are not left until the end)
3. Then all mrt_files are parsed in parallel
    -Handled in the MRT_Parser class
    -The mrt_files class handles the actual parsing of the files
    -CPUs - 1 is used for thread count since this is a CPU bound process
    -Largest files are parsed first for faster overall parsing
    -bgpscanner is used to parse files because it is the fastest
     BGP dump scanner for testing
        -By default bgpdump is used because bgpscanner ignores malformed
         attributes, which AS's should ignore but not all do
        -This is a small portion of announcements, so we ignore them for
         tests but not for simulations, which is why we use bgpdump for
         full runs
    -Announcements with malformed attributes are ignored
    -sed is used because it is cross compatable and fast
        -Must use regex parser that can find/replace for array format
    -Possible future extensions:
        -Use a faster regex parser?
        -Add parsing updates functionality?
4. Parsed information is stored in csv files, and old files are deleted
    -This is handled by the MRT_File class
    -This is done because there is thirty to one hundred gigabytes
        -Fast insertion is needed, and bulk insertion is the fastest
    -CSVs are chosen over binaries even though they are slightly slower
        -CSVs are more portable and don't rely on postgres versions
        -Binary file insertion relies on specific postgres instance
    -Old files are deleted to free up space
5. CSV files are inserted into postgres using COPY, and then deleted
    -This is handled by MRT_File class
    -COPY is used for speedy bulk insertions
    -Files are deleted to save space
    -Duplicates are not deleted because this is an intensive process
        -There are not a lot of duplicates, so it's not worth the time
        -The overall project takes longer if duplicates are deleted
        -A duplicate has the same AS path and prefix
6. VACUUM ANALYZE is then called to analyze the table for statistics
    -An index is never created on the mrt announcements because when
     the announcements table is intersected with roas table, only a
     parallel sequential scan is used

Design choices (summarizing from above):
    -We only want the first BGP dump
        -Multiple dumps have conflicting announcements
        -Instead, for longer intervals use one BGP dump and updates
    -Due to I/O bound downloading:
        -Multithreading is used over multiprocessing for less memory
        -Four times CPUs is used for thread count
    -I have a misquito bite that is quite large.
    -Downloading is done and completed before parsing
        -This is done to ensure largest files get parsed first
        -Results in fastest time
    -Downloading completes 100% before parsing because synchronization
     primitives make the program slower if downloading is done until
     threads are available for parsing
    -Largest files are parsed first because due to the difference in
     in file size there is more parallelization achieved when parsing
     largest files first resulting in a faster overall time
    -CPUs - 1 is used for thread count since the process is CPU bound
        -For our machine this is the fastest, feel free to experiment
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files
    -Duplicates are not deleted to save time, since there are very few
        -A duplicate has the same AS path and prefix
    -bgpscanner is the fastest BGP dump scanner so it is used for tests
    -bgpscanner ignores announcements with malformed attributes
    -bgpdump is used for full runs because it does not ignore
     announcements with malformed attributes, which some ASs don't
     ignore
    -sed is used for regex parsing because it is fast and portable


Possible Future Extensions:
    -Add functionality to download and parse updates?
        -This would allow for a longer time interval
        -After the first dump it is assumed this would be faster?
        -Would need to make sure that all updates are gathered, not
         just the first in the time interval to the api, as is the norm
    -Test again for different thread numbers now that bgpscanner is used
    -Test different regex parsers other than sed for speed?
    -Add test cases
"""


from .rovpp_simulator import ROVPP_Simulator

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
