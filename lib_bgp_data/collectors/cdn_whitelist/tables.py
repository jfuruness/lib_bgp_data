#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains CDN whitelist table"""

__authors__ = ["Tony Zheng"]
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from ...database import Generic_Table


class CDN_Whitelist_Table(Generic_Table):

    name = 'cdn_whitelist'

    columns = ['cdn', 'asn']

    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                 cdn varchar (200),
                 asn bigint
                 );"""
        self.cursor.execute(sql)
