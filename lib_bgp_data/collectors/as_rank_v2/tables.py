#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the table found on asrank.caida.org using
the Restful API.

This table inherits from Generic Table. For more information:
https://github.com/jfuruness/lib_bgp_data/wiki/Generic-Table
"""

__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

from ...utils.database import Generic_Table


class AS_Rank_V2(Generic_Table):
    """ASRankTable class, inherits from Generic_Table.
    For a more in depth explanation see the top of the file.
    """

    __slots__ = []

    name = 'as_rank_v2'
    columns = ['asn', 'organization', 'links']

    def _create_tables(self):
        """Creates new table if it doesn't already exist. The contents will
        be cleared everytime asrank_website_parser is run because information
        in the datebase may be out of date.
        """

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
              asn bigint,
              organization varchar (250),
              links bigint[]
              );"""
        self.cursor.execute(sql)
