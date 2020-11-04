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
        logging.info("Adding monitor to all MRT ann, ~20min")
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


class Control_Announcements_Table(Generic_Table):

    __slots__ = []

    name = "control_announcements"

    def fill_table(self):
        logging.info("getting intersection of control monitor ann prefixes "
                     "~10min")
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
               SELECT mrt.* FROM
                    {MRT_W_Monitors_Table.name} mrt
                INNER JOIN {Control_Monitors_Table.name} control_monitors
                    ON control_monitors.asn = mrt.monitor_asn
                INNER JOIN (
                    --gets all prefixes that occur at every asn
                    SELECT prefix FROM (
                        --gets all prefixes that occr from a monitor
                        SELECT prefix, COUNT(*) AS prefix_count
                            FROM {MRT_W_Monitors_Table.name} a
                        INNER JOIN {Control_Monitors_Table.name} b
                            ON a.monitor_asn = b.asn
                        GROUP BY prefix
                        ) prefixes_w_counts
                    WHERE prefixes_w_counts.prefix_count = (
                        SELECT COUNT(*) FROM {Control_Monitors_Table.name})
                ) prefix_intersection
                    ON prefix_intersection.prefix = mrt.prefix);"""

        self.execute(sql)

class Test_Announcements_Table(Generic_Table):

    __slots__ = []

    name = "test_announcements"

    def fill_table(self):
        logging.info("Getting all test announcements")
        logging.info("Getting distinct prefixes from control ann")
        control_prefix_name = "control_prefixes"
        sql = f"""CREATE UNLOGGED TABLE {control_prefix_name} AS (
              SELECT DISTINCT prefix
                FROM {Control_Announcements_Table.name}
              );"""
        self.execute(sql)
        logging.info("Getting all prefixes to exclude")
        excluded_prefixes_name = "excluded_prefixes"
        sql = f"""CREATE UNLOGGED TABLE {excluded_prefixes_name} AS (
              SELECT DISTINCT prefix FROM {MRT_Announcements_Table.name}
              EXCEPT SELECT prefix FROM {Control_Announcements_Table.name});"""
        self.execute(sql)
        sql = f"CREATE INDEX ON {excluded_prefixes_name}
              USING GIST(prefix inet_ops)"""
        self.execute(sql)
        
        logging.info("Version 1 for getting test ann")
        # Done this way to join as little as possible
        # Also if you just inner join with <<= you get duplication
        # Whereas with this method, it simply removes all cases where it's >>
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT mrt.* FROM {MRT_Announcements_Table.name} mrt
                LEFT JOIN {excluded_prefixes_name} ep
                    ON mrt.prefix = ep.prefix
                WHERE ep.prefix IS NULL);"""
        self.execute(sql)
        logging.info("Adding index to test_ann for exr input")
        sql = f"""CREATE INDEX ON {self.name} USING GIST(prefix inet_ops);"""
        self.execute(sql)

        logging.info("Trying the delete version")
        # Testing this way as well.
        # Rename mrt announcements table
        # Just delete all that don't abide by
        # Prob faster since don't need to recreate index for EXR splitting
        sql = f"""ALTER TABLE {MRT_Announcements_Table.name}
               RENAME TO {self.name}qqq;"""
        self.execute(sql)
        logging.info("Deleting from MRT ann")
        sql = f"""DELETE FROM {self.name}qqq a
              WHERE a.prefix = {excluded_prefixes_name}.prefix"""
        self.execute(sql)
        logging.info("Delete version complete")
        # THIRD METHOD
        # Just use MRT ann as your test ann
        # exr may take slightly longer, but who cares
        # esp if it is mostly the same size, and removing them takes forever
