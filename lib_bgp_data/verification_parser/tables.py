#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables for MRT generation for verification

These tables inherits from Database. The Database class allows for the
conection to a database upon initialization.

Possible future improvements:
    -Add test cases, docs, everything
"""


__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import logging

from ..database import Generic_Table


class Collectors_Table(Generic_Table):

    __slots__ = []

    def fill_table(self):
        logging.info("Getting collectors. This may take a while")
        # NOTE: postgres is 1 indexed, so as_path[1] is really first element
        sql = f"""SELECT DISTINCT as_path[1] AS collector_asn
               FROM {MRT_Announcements_Table.name};"""
        self.execute(sql)
