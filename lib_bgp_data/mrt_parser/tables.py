#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Announcements_Table

Announcements_Table inherits from the Generic_Table class. The Generic_Table
class allows for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function, because it would only ever be
used when combining with the roas table, which does a parallel seq_scan,
thus any indexes are not used since they are not efficient. Each table
follows the table name followed by a _Table since it inherits from the
database class.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

from ..database import Generic_Table


class MRT_Announcements_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "mrt_announcements"

    columns = ["prefix", "as_path", "origin", "time"]

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                 prefix cidr,
                 as_path bigint ARRAY,
                 origin bigint,
                 time bigint
                 );"""
        self.execute(sql)


class Distinct_Prefix_Origins_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "distinct_prefix_origins"

    columns = ["prefix", "origin"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT DISTINCT prefix, origin
                    FROM {MRT_Announcements_Table.name}
                );"""
        self.execute(sql)

class Distinct_Prefix_Origins_W_IDs_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "distinct_prefix_origins_w_ids"

    columns = ["prefix",
               "origin",
               "prefix_id",
               "origin_id",
               "prefix_origin_id",
               "prefix_group_id"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""WITH superprefixes AS(
                SELECT DISTINCT ON (prefix) dpo.prefix, prefix_id
                   FROM {Distinct_Prefix_Origins_Table.name} dpo
                    LEFT JOIN {Distinct_Prefix_Origins_Table.name} dpo2
                        ON dpo2.prefix << dpo.prefix
                    WHERE dpo2.prefix IS NULL
                ), superprefix_groups AS(
                    SELECT prefix,
                           ROW_NUMBER() OVER (ORDER BY prefix)
                                AS prefix_group_id
                    FROM superprefixes
                ), prefix_group_ids AS (
                    SELECT dpo.prefix, sp.prefix_group_id
                    FROM {Distinct_Prefix_Origins_Table.name} dpo
                        INNER JOIN superprefixes sp
                            ON sp.prefix <<= superprefixes
                ), block_ids AS (
                    SELECT DISTINCT block_id
                        FROM {Distinct_Prefix_Origins_Table.name}
                ), 
               CREATE UNLOGGED TABLE {self.name} AS (
                SELECT dpo.prefix,
                       dpo.origin,
                       prefix_ids.prefix_id,
                       origin_ids.origin_id,
                       prefix_origin_ids.prefix_origin_id,
                       prefix_group_ids.prefix_group_id
                FROM {Distinct_Prefix_Origins_Table.name} dpo
                INNER JOIN (
                    SELECT prefix,
                           ROW_NUMBER() OVER (ORDER BY prefix) AS prefix_id
                    FROM (SELECT DISTINCT prefix
                            FROM {Distinct_Prefix_Origins_Table.name})
                    ) prefix_ids
                        ON prefix_ids.prefix = dpo.prefix
                INNER JOIN (
                    SELECT origin,
                           ROW_NUMBER() OVER (ORDER BY origin) AS origin_id
                    FROM (SELECT DISTINCT origin
                            FROM {Distinct_Prefix_Origins_Table.name})
                    ) origin_ids
                        ON origin_ids.origin = dpo.origin
                INNER JOIN (
                    SELECT prefix, origin
                           ROW_NUMBER() OVER (ORDER BY prefix, origin) AS prefix_origin_id
                    FROM (SELECT DISTINCT prefix, origin
                            FROM {Distinct_Prefix_Origins_Table.name})
                    ) prefix_origin_ids
                        ON prefix_origin_ids.prefix = dpo.prefix
                            AND prefix_origin_ids.origin = dpo.origin
                INNER JOIN prefix_group_ids
                    ON prefix_group_ids.prefix = dpo.prefix
                );"""
        self.execute(sql)

class Blocks_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "blocks"

    columns = ["block_id", "group_id"]

    def _create_tables(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name}(
                block_id INTEGER
                group_id INTEGER
                );"""
        self.execute(sql)

class Prefix_Origin_Metadata_Table(Generic_Table):
    """Class with database functionality"""

    __slots__ = []


    name = "prefix_origin_metadata"

    def fill_table(self):
        sql = f"""WITH dpo_blocks AS (
                    SELECT dpo.prefix,
                           dpo.origin,
                           dpo.prefix_id,
                           dpo.origin_id,
                           dpo.prefix_origin_id,
                           dpo.prefix_group_id,
                           block.block_id
                    FROM {Distinct_Prefix_Origins_W_IDs_Table.name} dpo
                INNER JOIN {Blocks_Table.name} block
                    ON block.group_id = dpo.group_id
                ) dpo_blocks_roas AS (
                    SELECT dpo.prefix,
                           dpo.origin,
                           dpo.prefix_id,
                           dpo.origin_id,
                           dpo.prefix_origin_id,
                           dpo.prefix_group_id,
                           dpo.block_id,
                           CASE WHEN r.asn != dpo.origin
                                    THEN 2 --invalid by origin
                                WHEN MASKLEN(dpo.prefix) > r.max_length
                                    THEN 3 --invalid by max len
                                WHEN r.asn = dpo.origin
                                     AND MASKLEN(dpo.prefix) <= r.max_length
                                        THEN 1 --valid
                                ELSE 0 --unknown
                            END AS roa_validity
                    FROM dpo_blocks dpo
                    LEFT JOIN roas r
                        ON dpo.prefix <<= r.prefix
                )
                CREATE UNLOGGED TABLE {self.name} AS (
                SELECT dpo.prefix,
                       dpo.origin,
                       dpo.prefix_id,
                       dpo.origin_id
                       dpo.prefix_origin_id
                       dpo.prefix_group_id,
                       dpo.block_id,
                       dpo.roas,
                       bp_ids.block_prefix_id,
                       bo_ids.block_origin_id,
                       bpg.block_prefix_group_id,
                       bpo.block_prefix_origin_id
                FROM dpo_blocks_roas dpo
                INNER JOIN LATERAL (
                    SELECT dpo_t.prefix_origin_id,
                           ROW_NUMBER() OVER (ORDER BY block_id,
                                                       prefix)
                                AS block_prefix_id
                        FROM dpo_blocks_roas dpo_t
                    WHERE dpo_t.block_id = dpo.block_id
                ) block_prefix_ids bp_ids
                    ON bp_ids.prefix_origin_id = dpo.prefix_origin_id
                INNER JOIN LATERAL(
                    SELECT dpo_t.prefix_origin_id,
                           ROW_NUMBER() OVER (ORDER BY block_id,
                                                       origin)
                                AS block_origin_id
                        FROM dpo_blocks_roas dpo_t
                    WHERE dpo_t.block_id = dpo.block_id
                ) block_prefix_ids bp_ids
                    ON bp_ids.prefix_origin_id = dpo.prefix_origin_id
                INNER JOIN LATERAL(
                    SELECT dpo_t.prefix_origin_id,
                           ROW_NUMBER() OVER (ORDER BY block_id,
                                                       origin)
                                AS block_origin_id
                        FROM dpo_blocks_roas dpo_t
                        WHERE dpo_t.block_id = dpo.block_id
                ) block_prefix_ids bo_ids
                    ON bo_ids.prefix_origin_id = dpo.prefix_origin_id
                INNER JOIN LATERAL(
                    SELECT dpo_t.prefix_origin_id,
                           ROW_NUMBER() OVER (ORDER BY block_id,
                                                       group_id)
                                AS block_prefix_group_id
                        FROM dpo_blocks_roas dpo_t
                        WHERE dpo_t.block_id = dpo.block_id
                ) block_prefix_ids bpg_ids
                    ON bpg_ids.prefix_origin_id = dpo.prefix_origin_id
                INNER JOIN LATERAL(
                    SELECT dpo_t.prefix_origin_id,
                           ROW_NUMBER() OVER (ORDER BY block_id,
                                                       prefix_origin_id)
                                AS block_prefix_origin_id
                        FROM dpo_blocks_roas dpo_t
                        WHERE dpo_t2.block_id = dpo.block_id
                ) block_prefix_origin_ids bpo_ids
                    ON bpo_ids.prefix_origin_id = dpo.prefix_origin_id
            );"""
        self.execute(sql)
        with Distinct_Prefix_Origins_W_IDs_Table() as db:
            assert db.get_count() == self.get_count()

class MRT_W_Metadata_Table(Generic_Table):
    """Class with database functionality"""

    __slots__ = []


    name = "mrt_w_metadata"

    def fill_table(self):
        sql = """CREATE UNLOGGED TABLE {self.name} AS (
                SELECT mrt.*,
                       pom.prefix_id,
                       pom.origin_id
                       pom.prefix_origin_id
                       pom.prefix_group_id,
                       pom.block_id,
                       pom.roas,
                       pom.block_prefix_id,
                       pom.block_origin_id,
                       pom.block_prefix_group_id,
                       pom.block_prefix_origin_id,
                --NOTE that postgres starts at 1 not 0
                    mrt.as_path[1] AS monitor_asn
                FROM {MRT_Announcements_Table.name} mrt
                INNER JOIN {Prefix_Origin_Metadata_Table.name} pom
                    ON pom.prefix = mrt.prefix AND pom.origin = mrt.origin
                );"""
        self.execute(sql)
