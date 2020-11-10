#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Metadata_Parser

The purpose of this class is to prepare MRT files for extrapolator.
This is done through a series of steps.

Read README for in depth explanation.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

import bisect
import datetime
import logging
import os
import warnings

import psycopg2
import requests

from ..base_classes import Parser
from ..roas_parser.tables import ROAs_Table
from .mrt_file import MRT_File
from .mrt_installer import MRT_Installer
from .mrt_sources import MRT_Sources
from .tables import MRT_Announcements_Table
from .tables import Distinct_Prefix_Origins_Table
from .tables import Prefix_IDs_Table
from .tables import Origin_IDs_Table
from .tables import Prefix_Origin_IDs_Table
from .tables import Distinct_Prefix_Origins_W_IDs_Table
from .tables import Blocks_Table
from .tables import ROA_Known_Validity_Table
from .tables import ROA_Validity_Table
from .tables import Prefix_Origin_Blocks_Metadata_Table
from .tables import Prefix_Origin_Metadata_Table
from .tables import MRT_W_Metadata_Table
from ..utils import utils


class MRT_Metadata_Parser(Parser):
    """This class downloads, parses, and deletes files from Caida.

    In depth explanation at the top of module.
    """

    __slots__ = []

    def _run(self, *args, max_block_size=100):
        """Adds metadata to MRT files and prepares for EXR insertion

        1. Adds ROA state
        2. Adds prefix_id (id unique to each prefix)
        3. Adds monitor_asn (last ASN in the path)
        4. Adds block_id (block_id for insertion into exr
                          needed or else it won't fit in RAM)
        5. Adds block_prefix_id (prefix ids in block. Used to compare prefixes from
                                 in block in exr for determining best path
                                 since you can use this as a key in a list
                                 instead of a hashmap (inside extrapolator))
        6. JK, add as many indexes as you can think of. Used in Forecast,
            verification, Full path, etc, so just add them all.
        """

        self._validate()
        self._add_prefix_origin_index()
        logging.info(f"Creating {Distinct_Prefix_Origins_Table.name}")
#        self._get_p_o_table_w_indexes(Distinct_Prefix_Origins_Table)
        # If you were a real cool cat, you would have done a compressed
        # trie, finding common ancestors, to get prefix groupings
        # def way faster than all this. Also more difficult.
#        for Table in [Prefix_IDs_Table,
#                      Origin_IDs_Table,
#                      Prefix_Origin_IDs_Table,
#                      Distinct_Prefix_Origins_W_IDs_Table]:
#            logging.info(f"Creating {Table.__name__}")
#            self._get_p_o_table_w_indexes(Table)
#        self._create_block_table(max_block_size)
#        self._add_roas_index()
#        for Table in [ROA_Known_Validity_Table,
#                      ROA_Validity_Table,
#                      Prefix_Origin_Blocks_Metadata_Table,
#                      Prefix_Origin_Metadata_Table]:
#            self._get_p_o_table_w_indexes(Table)
        self._add_metadata()

    def _validate(self):
        """Asserts that tables are filled"""

        for Table in [MRT_Announcements_Table, ROAs_Table]:
            with Table() as db:
                err = f"{db.name} not filled"
                sql = f"SELECT * FROM {db.name} LIMIT 2"
                assert len(db.execute(sql)) > 0, err

    def _add_prefix_origin_index(self):
        """Adds index to prefix and origin for combining with ROAs table"""

        with MRT_Announcements_Table() as db:
            sql = f"""CREATE INDEX IF NOT EXISTS {db.name}_po_index ON
                  {db.name} USING GIST(prefix inet_ops, origin)"""
            self._create_index(sql, db)
            sql = f"""CREATE INDEX IF NOT EXISTS {db.name}_po_btree_i ON
                    {db.name}(prefix inet_ops, origin);"""
            self._create_index(sql, db)

    def _get_p_o_table_w_indexes(self, Table):
        """Prefix origin table with indexes"""

        with Table(clear=True) as db:
            db.fill_table()
            index_sqls = [
                  f"""CREATE INDEX IF NOT EXISTS {db.name}_dpo_index
                  ON {db.name} USING GIST(prefix inet_ops, origin)""",

                  f"""CREATE INDEX IF NOT EXISTS {db.name}_dist_p_index
                  ON {db.name} USING GIST(prefix inet_ops)""",

                  f"""CREATE INDEX IF NOT EXISTS {db.name}_dist_o_index
                  ON {db.name}(origin)""",

                  f"""CREATE INDEX IF NOT EXISTS {db.name}_g_index
                      ON {db.name}(prefix_group_id);""",
                  f"""CREATE INDEX IF NOT EXISTS {db.name}_pbtree_index
                      ON {db.name}(prefix)""",
                  f"""CREATE INDEX IF NOT EXISTS {db.name}_po_btree_index
                     ON {db.name}(prefix, origin);"""
            ]
            for sql in index_sqls:
                try:
                    self._create_index(sql, db)
                except psycopg2.errors.UndefinedColumn:
                    pass

    def _create_block_table(self, max_block_size):
        """Creates iteration blocks as balanced as possible

        Based on prefix, total # ann for that prefix
        Needed to write a custom algo for this
        but it's fine, since binpacking is already np hard
        Figures out first correct number of bins, since prefixes
        are most important
        Then figures out which bin to place in
        Largest ann_count first into smallest bin_weight
        """

        class Bin:
            def __init__(self, bin_id):
                self.bin_id = bin_id
                self.prefixes = []
                self.total_weight = 0

            def add_prefix(self, prefix, ann_count):
                if len(self.prefixes) + 1 <= max_block_size:
                    self.prefixes.append(prefix)
                    self.total_weight += ann_count
                    return True
                else:
                    return False

            def __lt__(self, other):
                if isinstance(other, self.__class__):
                    return self.total_weight < other.total_weight

            @property
            def rows(self):
                return [[self.bin_id, x] for x in self.prefixes]

        logging.info("Getting prefix blocks")
        with Prefix_IDs_Table() as db:
            group_counts = [[x["prefix"], x["ann_count"]]
                            for x in db.get_all()]
            group_counts = sorted(group_counts, key=lambda x: x[1], reverse=True)
            bin_count = (len(group_counts) // max_block_size) + 1
            bins = list(sorted([Bin(i) for i in range(bin_count)]))
            # tbh, is this the same as just doing it in order?
            # Should check this...
            for i, (prefix, ann_count) in enumerate(group_counts):
                for b_index, b in enumerate(bins):
                    if b.add_prefix(prefix, ann_count):
                        current_index = b_index
                        break
                # Inserts item in sorted list correctly
                # MUCH faster than sort
                # https://stackoverflow.com/a/38346428/8903959
                bisect.insort_left(bins, bins.pop(b_index))
            block_table_rows = []
            for current_bin in bins:
                block_table_rows.extend(current_bin.rows)
            csv_path = os.path.join(self.csv_dir, "block_table.csv")
            utils.rows_to_db(block_table_rows, csv_path, Blocks_Table)
            for _id in ["block_id", "prefix"]:
                sql = f"""CREATE INDEX IF NOT EXISTS
                        {Blocks_Table.name}_{_id}
                            ON {Blocks_Table.name}({_id})
                      ;"""
                self._create_index(sql, db)

    def _add_roas_index(self):
        """Creates an index on the roas table"""

        with ROAs_Table() as db: 
            sql = f"""CREATE INDEX IF NOT EXISTS roas_index
                  ON {db.name} USING GIST(prefix inet_ops, asn);"""
            self._create_index(sql, db)

    def _add_metadata(self):
        """Joins prefix origin metadata with MRT Anns"""

        logging.info("Adding metadata to the MRT announcements")
        with MRT_W_Metadata_Table(clear=True) as db:
            db.fill_table()
            sql = f"""CREATE INDEX {db.name}_block_index
                    ON {db.name}(block_id);"""
            self._create_index(sql, db)
            # NOTE: you probably need other indexes on this table
            # Depending on what application is being run

    def _create_index(self, sql, db):
        logging.info(f"Creating index on {db.name}")
        db.execute(sql)
        logging.info("Index complete")

################
### Old Code ###
################

    def _create_block_table_w_prefix_groups(self, max_block_size):
        """Legacy code now

        This can be used for creating blocks with groups
        We didn't need to tackle this problem for our phd
        We leave it for the next runner up.

        Creates blocks for the extrapolator

        1. Counts number of prefixes per group
        2. Packs them into blocks with a fixed max size
        3. Creates the block id table
            -contains group_id, block_id
        """

        logging.info("Getting prefix blocks")
        with Distinct_Prefix_Origins_W_IDs_Table() as db:
            sql = f"""SELECT prefix_group_id, COUNT(prefix_group_id) AS total
                  FROM {db.name}
                    GROUP BY prefix_group_id;"""
            group_counts = db.execute(sql)
            group_counts_dict = {x["prefix_group_id"]: x["total"]
                                 for x in group_counts}
            # Returns a list of dicts, that contains group_id: count
            bins = binpacking.to_constant_volume(group_counts_dict, max_block_size)
            block_table_rows = []
            for block_id, current_bin in enumerate(bins):
                for group_id in current_bin:
                    block_table_rows.append([block_id, group_id])
            csv_path = os.path.join(self.csv_dir, "block_table.csv")
            utils.rows_to_db(block_table_rows, csv_path, Blocks_Table)
            for _id in ["block_id", "prefix_group_id"]:
                sql = f"""CREATE INDEX IF NOT EXISTS
                        {Blocks_Table.name}_{_id} ON {Blocks_Table.name}({_id})
                      ;"""
                self._create_index(sql, db)

