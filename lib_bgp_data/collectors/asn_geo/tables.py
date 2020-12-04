#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from ...utils.database import Generic_Table


class ASN_Geo_Table(Generic_Table):

    name = "asn_geo"

    columns = ['asn', 'country', 'continent']

    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
              asn bigint,
              country varchar(2),
              continent varchar(2));"""

        self.cursor.execute(sql)

    def create_index(self):
        sql = f"CREATE UNIQUE INDEX asn_idx ON {self.name} (asn);"
