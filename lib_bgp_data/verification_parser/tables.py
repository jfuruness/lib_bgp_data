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

from ..asrank_website_parser.tables import ASRankTable
from ..database import Generic_Table
from ..mrt_parser.tables import MRT_Announcements_Table


class Collectors_Table(Generic_Table):

    __slots__ = []

    name = "collectors"

    def fill_table(self):
        logging.info("Getting collectors. Takes <= 10 min ish")
        # NOTE: postgres is 1 indexed, so as_path[1] is really first element
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT DISTINCT as_path[1] AS collector_asn
               FROM {MRT_Announcements_Table.name});"""
        self.execute(sql)

class Top_100_Collectors_Table(Generic_Table):

    __slots__ = []

    name = "top_100_collectors"

    def fill_table(self):
        logging.info("Getting top collectors by as rank")
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT collector_asn, as_rank FROM {Collectors_Table.name} c
                    INNER JOIN {ASRankTable.name} asr
                        ON asr.as_number = c.collector_asn
                ORDER BY as_rank LIMIT 100);"""
        self.execute(sql)

class Top_100_w_100k_Prefixes_Table(Generic_Table):

    __slots__ = []

    name = "top_100_collectors_w_100k_prefixes"

    def fill_table(self):
        logging.info("Filtering collectors by having over 100k prefixs")
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT * FROM (
                    SELECT collector_asn, as_rank, COUNT(*) as num_prefixes
                        FROM {MRT_Announcements_Table.name} mrt
                        INNER JOIN {Top_100_Collectors_Table.name} c
                    ON c.collector_asn = mrt.as_path[1]
                    GROUP BY c.collector_asn, as_rank) placeholder
                WHERE num_prefixes > 100000);"""
        self.execute(sql)
