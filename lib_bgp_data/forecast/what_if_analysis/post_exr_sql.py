#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains sql to be run after the extrapolator"""

from .sql_utils import Policies, Validity
from .sql_utils import create_gist, create_index, create_btree
from .sql_utils import create_table_w_gist
from .sql_utils import create_table_w_btree
from .sql_utils import create_table_w_btree_asn

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

def get_post_exr_sql():

    # MUST BE IN EPOCH!!!!!!
    all_sql = []

    return all_sql

"""
def get_post_exr_sql():

    1/0 RESTART DB!!!!

    all_sql = []
    exr_indexes = []
    for col in ["mrt_index", "extra_mrt_index", "asn"]:
        exr_indexes.append(create_index("exr_results", col))
    all_sql.extend(exr_indexes)

    all_sql.extend(
        create_table_w_btree_asn(
            "all_asns",
            "SELECT DISTINCT asn from exr_results"))

    all_sql.append("VACUUM ANALYZE")

DROP TABLE IF EXISTS invalid_asn_hijacked_no_superprefix_counts;
CREATE UNLOGGED TABLE IF NOT EXISTS invalid_asn_hijacked_no_superprefix_counts AS (
    SELECT exr.asn, COUNT(*) FROM exr_results exr
        INNER JOIN invalid_asn_hijacked_ann_indexes ih
            ON ih.mrt_index = exr.mrt_index
        INNER JOIN exr_results exr2
            ON exr2.asn = exr.asn
        LEFT JOIN invalid_asn_extra_ann_indexes ie
            ON ie.mrt_index = exr.mrt_index AND exr2.mrt_index = ie.extra_mrt_index
        WHERE ie.mrt_index IS NULL
        GROUP BY exr.asn);
CREATE INDEX ON invalid_asn_hijacked_no_superprefix_counts(asn)

DROP TABLE IF EXISTS invalid_asn_hijacked_counts;
CREATE UNLOGGED TABLE IF NOT EXISTS invalid_asn_hijacked_counts AS (
    SELECT exr.asn, COUNT(*) FROM exr_results exr
        INNER JOIN invalid_asn_hijacked_ann_indexes ih
            ON ih.mrt_index = exr.mrt_index
        GROUP BY exr.asn);
CREATE INDEX ON invalid_asn_hijacked_counts(btree)

DROP TABLE IF EXISTS invalid_asn_not_hijacked_no_superprefix_counts;
CREATE UNLOGGED TABLE IF NOT EXISTS invalid_asn_not_hijacked_no_superprefix_counts AS (
    SELECT exr.asn, COUNT(*) FROM exr_results exr
        INNER JOIN invalid_asn_not_hijacked_ann_indexes inh
            ON inh.mrt_index = exr.mrt_index
        INNER JOIN exr_results exr2
            ON exr2.asn = exr.asn
        LEFT JOIN invalid_asn_extra_ann_indexes ie
            ON ie.mrt_index = exr.mrt_index AND exr2.mrt_index = ie.extra_mrt_index
        WHERE ie.mrt_index IS NULL
        GROUP BY exr.asn);
CREATE INDEX ON invalid_asn_not_hijacked_no_superprefix_counts(asn);

DROP TABLE IF EXISTS invalid_asn_not_hijacked_counts;
CREATE TABLE IF NOT EXISTS invalid_asn_not_hijacked_counts AS (
    SELECT exr.asn, COUNT(*) FROM exr_results exr
        INNER JOIN invalid_asn_hijacked_ann_indexes inh
            ON inh.mrt_index = exr.mrt_index
        GROUP BY exr.asn);
CREATE INDEX ON invalid_asn_not_hijacked_counts(asn);

DROP TABLE IF EXISTS valid_asn_hijacked_counts;
CREATE TABLE IF NOT EXISTS valid_asn_hijacked_counts AS (
    SELECT exr.asn, COUNT(*) FROM exr_results exr
        INNER JOIN valid_asn_hijacked_ann_indexes inh
            ON inh.mrt_index = exr.mrt_index
        GROUP BY exr.asn);
CREATE INDEX ON valid_asn_hijacked_counts(asn);

DROP TABLE IF EXISTS asn_policy_stats
CREATE TABLE asn_policy_stats AS (
    SELECT a.asn,
        b.count AS invalid_asn_hijacked_no_superprefix
        c.count - b.count AS invalid_asn_hijacked_yes_superprefix
        d.count AS invalid_asn_not_hijacked_no_superprefix
        e.count - d.count AS invalid_asn_not_hijacked_yes_superprefix
        f.count AS valid_asn_hijacked
    FROM all_asns a
    INNER JOIN invalid_asn_hijacked_no_superprefix_counts b
        ON a.asn = b.asn
    INNER JOIN invalid_asn_hijacked_counts c
        ON a.asn = c.asn
    INNER JOIN invalid_asn_not_hijacked_no_superprefix_counts d
        ON a.asn = d.asn
    INNER JOIN invalid_asn_not_hijacked_counts e
        ON a.asn = e.asn
    INNER JOIN valid_asn_hijacked_counts f
        on a.asn = f.asn);
CREATE INDEX ON asn_policy_stats(asn);
"""
