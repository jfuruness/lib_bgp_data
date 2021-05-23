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

from ..mrt_base.tables import MRT_Announcements_Table

from ....utils.base_classes import ROA_Validity
from ....utils.database import Generic_Table


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

class Prefix_IDs_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "prefix_ids"

    columns = ["prefix", "ann_count", "prefix_id"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                    SELECT prefix,
                           ann_count,
                           ROW_NUMBER() OVER () -1 AS prefix_id
                    FROM (
                         SELECT mrt.prefix,
                                COUNT(*) AS ann_count
                        FROM {MRT_Announcements_Table.name} mrt
                            GROUP BY mrt.prefix) a
                );""" 
        self.execute(sql)

class Origin_IDs_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "origin_ids"

    columns = ["origin", "origin_id"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                        SELECT origin, ROW_NUMBER() OVER () -1 AS origin_id
                            FROM (
                             SELECT DISTINCT origin
                            FROM {Distinct_Prefix_Origins_Table.name} dpo
                        ) a
                );""" 
        self.execute(sql)

class Prefix_Origin_IDs_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "prefix_origin_ids"

    columns = ["prefix", "origin", "prefix_origin_id"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                        --table id distinct already, no distinct nessecary
                         SELECT dpo.origin, dpo.prefix,
                                         ROW_NUMBER() OVER () -1
                                            AS prefix_origin_id
                        FROM {Distinct_Prefix_Origins_Table.name} dpo
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
               "prefix_origin_id"]

    def fill_table(self):
        """Fills table with data"""

        # NOTE: I know you can use with statements for superprefix tables/
        # group ids, but this makes the query too slow without indexes
        sql = f"""
                CREATE UNLOGGED TABLE {self.name} AS (
                SELECT dpo.prefix,
                       dpo.origin,
                       p_ids.prefix_id,
                       o_ids.origin_id,
                       dpo.prefix_origin_id,
                       0 AS prefix_group_id --prefix_group_ids.prefix_group_id
                FROM {Prefix_Origin_IDs_Table.name} dpo
                INNER JOIN {Prefix_IDs_Table.name} p_ids
                    ON p_ids.prefix = dpo.prefix
                INNER JOIN {Origin_IDs_Table.name} o_ids
                    ON o_ids.origin = dpo.origin
                );"""
        self.execute(sql)

class Blocks_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "blocks"

    columns = ["block_id", "prefix"]

    def _create_tables(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name}(
                block_id INTEGER,
                prefix CIDR
                );"""
        self.execute(sql)

# NOTE 0 valid, 1 unknown, 2 invalid by origin, 3 invalid by length

class ROA_Known_Validity_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "roa_known_validity"

    columns = ["prefix", "origin", "roa_validity"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                    SELECT dpo.prefix,
                           dpo.origin,
                           --NOTE: don't change the numbering. It's dependent elsewhere as well
                           CASE WHEN r.asn != dpo.origin AND MASKLEN(dpo.prefix) > r.max_length
                                    THEN {ROA_Validity.INVALID_BY_ALL.value}
                                WHEN MASKLEN(dpo.prefix) > r.max_length
                                    THEN {ROA_Validity.INVALID_BY_LENGTH.value}
                                WHEN r.asn != dpo.origin
                                    THEN {ROA_Validity.INVALID_BY_ORIGIN.value}
                                WHEN r.asn = dpo.origin
                                     AND MASKLEN(dpo.prefix) <= r.max_length
                                        THEN {ROA_Validity.VALID.value} --valid
                                ELSE {ROA_Validity.UNKNOWN.value} --unknown
                            END AS roa_validity
                    FROM {Distinct_Prefix_Origins_W_IDs_Table.name} dpo
                    INNER JOIN (SELECT prefix,
                                      asn,
                                      max_length
                               FROM roas WHERE (SELECT MAX(created_at)
                                                FROM roas) = created_at) r
                        ON dpo.prefix <<= r.prefix
                );"""
        self.execute(sql)

        # If there are overlapping ROAs, keep the most valid one
        # https://stackoverflow.com/a/6584134
        sql = f"""DELETE FROM {self.name} a USING (
                SELECT MIN(roa_validity) AS roa_validity, prefix, origin
                    FROM {self.name}
                    GROUP BY prefix, origin HAVING COUNT(*) > 1
                ) b
                WHERE a.prefix = b.prefix
                    AND a.origin = b.origin
                    AND a.roa_validity != b.roa_validity"""
        self.execute(sql)

        # https://stackoverflow.com/a/6584134
        # In case there are any other duplicates, remove them
        sql = f"""DELETE FROM {self.name} a USING (
                SELECT MIN(ctid) as ctid, prefix, origin, roa_validity FROM {self.name}
                GROUP BY prefix, origin, roa_validity HAVING COUNT(*) > 1
                ) b
                WHERE a.prefix = b.prefix AND a.origin = b.origin AND
                    a.roa_validity = b.roa_validity AND a.ctid <> b.ctid;"""
        self.execute(sql)

class ROA_Validity_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "roa_validity"

    columns = ["prefix", "origin", "roa_validity"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} AS (
                    SELECT prefix, origin, roa_validity
                        FROM {ROA_Known_Validity_Table.name}
                    UNION ALL
                    (SELECT prefix, origin, {ROA_Validity.UNKNOWN.value} AS roa_validity
                        FROM {Distinct_Prefix_Origins_W_IDs_Table.name}
                    EXCEPT SELECT prefix, origin, {ROA_Validity.UNKNOWN.value} AS roa_validity
                        FROM {ROA_Known_Validity_Table.name})
                );"""
        self.execute(sql)

class Prefix_Origin_Blocks_Metadata_Table(Generic_Table):
    """Class with database functionality"""

    __slots__ = []


    name = "prefix_origin_block_metadata"

    def fill_table(self):
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                    SELECT dpo.prefix,
                           dpo.origin,
                           dpo.prefix_id,
                           dpo.origin_id,
                           dpo.prefix_origin_id,
                           block.block_id,
                           roa_v.roa_validity
                    FROM {Distinct_Prefix_Origins_W_IDs_Table.name} dpo
                INNER JOIN {Blocks_Table.name} block
                    ON block.prefix = dpo.prefix
                INNER JOIN {ROA_Validity_Table.name} roa_v
                    ON roa_v.prefix = dpo.prefix AND roa_v.origin = dpo.origin
                );"""
        self.execute(sql)
 



class Prefix_Origin_Metadata_Table(Generic_Table):
    """Class with database functionality"""

    __slots__ = []


    name = "prefix_origin_metadata"

    def fill_table(self):
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT dpo.prefix,
                       dpo.origin,
                       dpo.prefix_id,
                       dpo.origin_id,
                       dpo.prefix_origin_id,
                       --dpo.prefix_group_id,
                       dpo.block_id,
                       dpo.roa_validity,
                       bp_ids.block_prefix_id
                       --bo_ids.block_origin_id,
                       --bpg_ids.block_prefix_group_id,
                       --bpo_ids.block_prefix_origin_id
                FROM {Prefix_Origin_Blocks_Metadata_Table.name} dpo
                INNER JOIN (
                    --must do lateral rather than partition to get proper distinct
                    SELECT DISTINCT prefix,
                           DENSE_RANK() OVER (PARTITION BY block_id ORDER BY prefix) - 1 AS block_prefix_id
                        FROM {Prefix_Origin_Blocks_Metadata_Table.name}
                ) bp_ids
                    ON bp_ids.prefix = dpo.prefix
                --NOTE that later if needed you can add block_origin_id, etc
                --but to save time, and since they currently have no use,
                --we omit them here for speed.
                --INNER JOIN (
                --    SELECT DISTINCT origin,
                --           DENSE_RANK() OVER (PARTITION BY block_id ORDER BY origin) - 1 AS block_origin_id
                --        FROM {Prefix_Origin_Blocks_Metadata_Table.name}
                --) bo_ids
                --    ON bo_ids.origin = dpo.origin
                --INNER JOIN (
                --    SELECT DISTINCT prefix_group_id,
                --           DENSE_RANK() OVER (PARTITION BY block_id ORDER BY prefix_group_id) - 1
                --                AS block_prefix_group_id
                --        FROM {Prefix_Origin_Blocks_Metadata_Table.name}
                --) bpg_ids
                --    ON bpg_ids.prefix_group_id = dpo.prefix_group_id
                --INNER JOIN (
                --    SELECT prefix, origin,
                --           DENSE_RANK() OVER (PARTITION BY block_id ORDER BY prefix, origin) - 1
                --                AS block_prefix_origin_id
                --        FROM {Prefix_Origin_Blocks_Metadata_Table.name}
                --) bpo_ids
                --    ON bpo_ids.prefix = dpo.prefix AND bpo_ids.origin = dpo.origin
            );"""
        self.execute(sql)
        with Distinct_Prefix_Origins_W_IDs_Table() as db:
            assert db.get_count() == self.get_count()

class MRT_W_Metadata_Table(Generic_Table):
    """Class with database functionality"""

    __slots__ = []


    name = "mrt_w_metadata"

    columns = ["prefix", "as_path", "origin", "time", "monitor_asn",
               "prefix_id", "origin_id", "prefix_origin_id", "block_id",
               "roa_validity", "block_prefix_id", "origin_hijack_asn"]

    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name}(
                prefix CIDR,
                as_path BIGINT[],
                origin BIGINT,
                time BIGINT,
                monitor_asn BIGINT,
                prefix_id BIGINT,
                origin_id BIGINT,
                prefix_origin_id BIGINT,
                block_id INTEGER,
                roa_validity SMALLINT,
                block_prefix_id INTEGER,
                origin_hijack_asn BIGINT
               );"""
        self.execute(sql)

    def fill_table(self):
        self.execute(f"DROP TABLE IF EXISTS {self.name}")
        self.execute("ANALYZE")
        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                SELECT mrt.*,
                       --NOTE that postgres starts at 1 not 0
                       mrt.as_path[1] AS monitor_asn,
                       pom.prefix_id,
                       pom.origin_id,
                       pom.prefix_origin_id,
                       --pom.prefix_group_id,
                       pom.block_id,
                       pom.roa_validity,
                       pom.block_prefix_id,
                       NULL AS origin_hijack_asn--,
                       --pom.block_origin_id,
                       --pom.block_prefix_group_id,
                       --pom.block_prefix_origin_id
                FROM {MRT_Announcements_Table.name} mrt
                INNER JOIN {Prefix_Origin_Metadata_Table.name} pom
                    ON pom.prefix = mrt.prefix AND pom.origin = mrt.origin
                );"""
        self.execute(sql)



##################
### Old Tables ###
##################

# These were some old tables when we initially wanted to do the mrt anns
# and have each iteration in exr be from the same prefix group
# But we didn't need to for our phd
# I leave them here for the next person to tackle that problem




class Superprefixes_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "superprefixes"

    columns = ["prefix"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                    SELECT DISTINCT ON (prefix) dpo.prefix
                       FROM {Prefix_IDs_Table.name} dpo
                        LEFT JOIN {Prefix_IDs_Table.name} dpo2
                            ON dpo2.prefix >> dpo.prefix
                        WHERE dpo2.prefix_id IS NULL);"""
        self.execute(sql)

class Superprefix_Groups_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "superprefix_groups"

    columns = ["prefix", "prefix_group_id"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                        SELECT prefix, ROW_NUMBER() OVER () - 1
                                    AS prefix_group_id
                        FROM {Superprefixes_Table.name}
                );""" 
        self.execute(sql)

class Unknown_Prefixes_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "unknown_prefixes"

    columns = ["prefix"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                        SELECT prefix FROM {Prefix_IDs_Table.name}
                        EXCEPT
                        SELECT prefix FROM {Superprefixes_Table.name}
                );""" 
        self.execute(sql)


class Prefix_Groups_Table(Generic_Table):
    """Class with database functionality

    in depth explanation at the top of the file"""

    __slots__ = []

    name = "prefix_groups"

    columns = ["prefix", "prefix_group_id"]

    def fill_table(self):
        """Fills table with data"""

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS(
                         SELECT u_p.prefix, spg.prefix_group_id
                        FROM {Unknown_Prefixes_Table.name} u_p
                        INNER JOIN {Superprefix_Groups_Table.name} spg
                            ON u_p.prefix << spg.prefix
                        UNION ALL
                        SELECT prefix, prefix_group_id
                            FROM {Superprefix_Groups_Table.name}
                );""" 
        self.execute(sql)



