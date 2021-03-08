#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains classes for ASN Lookup

All of these tables inherit from the Database class. The Database
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. Each table
follows the table name followed by a _Table since it inherits from the
database class.
"""


__author__ = "Samarth Kasbawala"
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from ...utils.database import Generic_Table


class ASN_Metadata_Table(Generic_Table):
    """Announcements table class"""

    __slots__ = []

    name = "asn_metadata"
    columns = ["asn",
               "ip",
               "continent",
               "country",
               "most_specific_subdiv",
               "city",
               "latitude",
               "longitude"]

    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
              asn bigint,
              ip cidr,
              continent char(2),
              country char(2),
              most_specific_subdiv varchar(3),
              city varchar(20),
              latitude real,
              longitude real
              ) ;"""
        self.execute(sql)
