#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from ..database import Generic_Table


class Historical_ROAS_Table(Generic_Table):

    name = "historical_roas"

    def _create_tables(self):
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS historical_roas (
                 asn integer,
                 prefix cidr,
                 maxlength smallint,
                 notbefore timestamp,
                 notafter timestamp);"""
        self.execute(sql)


