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
    columns = ['asn', 'prefix', 'maxlen', 'notbefore', 'notafter', 'date_added']

    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                  asn bigint,
                  prefix cidr,
                  maxlen smallint,
                  notbefore timestamp,
                  notafter timestamp,
                  date_added date);"""
        self.execute(sql)

    def delete_duplicates(self):
        """Deletes duplicated roas, preserving earlier one."""

        sql = f"""DELETE FROM {self.name} a
                    USING     {self.name} b
                  WHERE a.date_added > b.date_added
                    AND a.asn = b.asn
                    AND a.prefix = b.prefix
                    AND a.maxlen = b.maxlen
                    AND a.notbefore = b.notbefore
                    AND a.notafter = b.notafter;"""
        self.execute(sql)

    def create_index(self):
        index_name = f'{self.name}_index'

        # if adding lots of data, it's faster to recreate than update
        sql = f"DROP INDEX IF EXISTS {index_name}"
        self.execute(sql)

        sql = f"""CREATE INDEX IF NOT EXISTS {self.name}_index
                    ON {self.name}(prefix, date_added)"""
        self.execute(sql)

class Historical_ROAS_Parsed_Table(Generic_Table):

    name = 'historical_roas_parse'
    
    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                    file text
                    );"""
        self.execute(sql)


