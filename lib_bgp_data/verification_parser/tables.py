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


class MRT_W_Monitors_Table(Generic_Table):

    __slots__ = []

    name = "mrt_w_monitors"

    def fill_table(self):
        # Add to design decisions - updating table takes forever, which is why the rewrite
        # Note that this may be because I already had an index on it, but whatevs
        logging.info("Adding monitor to all MRT ann, was ~20min.")

        # NOTE: postgres is 1 indexed, so as_path[1] is really first element
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT as_path[1] AS monitor_asn,
                       prefix,
                       as_path,
                       origin,
                       time
                FROM {MRT_Announcements_Table.name}
                );"""
        self.execute(sql)
        logging.info("Creating index on the prefix")
        sql = f"""CREATE INDEX ON {self.name} USING GIST(prefix inet_ops);"""
        self.execute(sql)
        logging.info("Creating index on the monitor")
        self.execute(f"CREATE INDEX ON {self.name}(monitor)")

        msg = "MRT Announcements not filled"
        assert len(self.execute(f"SELECT * FROM {self.name} LIMIT 2")) > 1, msg

class Monitors_Table(Generic_Table):

    __slots__ = []

    name = "monitors"

    def fill_table(self):
        logging.info("Getting Monitors and their statistics, ~37m")
        with ASRankTable() as db:
            largest_as_rank_plus_one = db.get_count() + 1
        # Yes, this takes a long time.
        # And if we were just taking best monitors, I'd agree it could be faster
        # But this table is often referenced for stats
        # So it must remain this way
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                --NOTE: ann stands for announcements
                SELECT distinct_prefixes.monitor_asn AS asn,
                        --coalesced since as_rank doesn't have all ases
                       COALESCE(asrank.as_rank, {largest_as_rank_plus_one}) AS as_rank,
                       distinct_prefixes.distinct_prefixes_count
                            AS distinct_prefixes,
                       total_anns.total_ann_count AS total_ann,
                       total_anns.total_ann_count
                            - distinct_prefixes.distinct_prefixes_count
                                AS extra_ann
                FROM
                    (SELECT monitor_asn,
                            COUNT(DISTINCT prefix) AS distinct_prefixes_count
                     FROM {MRT_W_Monitors_Table.name}
                        GROUP BY monitor_asn) distinct_prefixes
                --NOTE for later, could prob be optimized to not group twice?
                INNER JOIN
                     (SELECT monitor_asn,
                            COUNT(*) AS total_ann_count
                     FROM {MRT_W_Monitors_Table.name}
                        GROUP BY monitor_asn) total_anns
                    ON
                        distinct_prefixes.monitor_asn = total_anns.monitor_asn
                LEFT JOIN
                    {ASRankTable.name}
                ON
                    asrank.as_number = distinct_prefixes.monitor_asn
            );"""
        self.execute(sql)

class Control_Monitors_Table(Generic_Table):

    __slots__ = []

    name = "control_monitors"
    control_total = 10

    def fill_table(self):
        logging.info("Getting control Monitors\n")
        logging.info("Must have >800k ann and only have ribout")
        logging.info(f"Sort by as rank and pick top {self.control_total}")
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT * FROM {Monitors_Table.name}
                --No extra announcements means rib out
                WHERE extra_ann = 0 AND total_ann >= 800000
                ORDER BY as_rank
                LIMIT {self.control_total}
                );"""
        self.execute(sql)
