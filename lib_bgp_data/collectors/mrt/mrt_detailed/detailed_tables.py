#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Detailed_Table, mirroring the form
and operation of MRT_Announcements_Table and adding a few more columns
to it for more information.
"""

__author__ = "Nicholas Shpetner"
__credits__ = ["Justin Furuness, Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Nicholas Shpetner"
__email__ = "nicholas.shpetner@uconn.edu"
__status__ = "Development"

import logging
from ..database import Generic_Table


class MRT_Detailed_Table(Generic_Table):
    """Class with database functionality.
    """

    __slots__ = []

    name = "mrt_detailed"

    #columns = ['update_type', 'prefix', 'as_path', 'origin',
    #            'time', 'interval_start', 'interval_end']

    columns = ['interval_end', 'interval_start', 'time', 'origin', 'prefix', 'as_path', 'update_type']

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        #sql = """CREATE UNLOGGED TABLE IF NOT EXISTS mrt_detailed (update_type text,
        #                                                           prefix cidr,
        #                                                           as_path bigint ARRAY,
        #                                                           origin bigint,
        #                                                           time bigint,
        #                                                           interval_start bigint,
        #                                                           interval_end bigint);"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS mrt_detailed (interval_end bigint,
                                                                   interval_start bigint,
                                                                   time bigint,
                                                                   origin bigint,
                                                                   prefix cidr,
                                                                   as_path bigint ARRAY,
                                                                   update_type text);"""

        self.execute(sql)
