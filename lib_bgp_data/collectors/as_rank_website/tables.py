#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the table found on asrank.caida.org.

This table inherits from Generic Table. For more information:
https://github.com/jfuruness/lib_bgp_data/wiki/Generic-Table
"""

__author__ = "Abhinna Adhikari, Justin Furuness"
__credits__ = ["Abhinna Adhikari", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

from ...utils.database import Generic_Table


class AS_Rank_Table(Generic_Table):
    """ASRankTable class, inherits from Generic_Table.
    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = 'as_rank'
    columns = ['as_rank', 'asn', 'organization', 'country', 'cone_size']

    def _create_tables(self):
        """Creates new table if it doesn't already exist. The contents will
        be cleared everytime asrank_website_parser is run because information
        in the datebase may be out of date.
        """

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
              as_rank bigint,
              asn bigint,
              organization varchar (250),
              country varchar (2),
              cone_size integer
              );"""
        self.cursor.execute(sql)

    def get_top_100_ases(self):
        """Returns top 100 ases by as rank"""

        sql = f"""SELECT * FROM {self.name} ORDER BY as_rank LIMIT 100;"""
        return [x["as_number"] for x in self.execute(sql)]
