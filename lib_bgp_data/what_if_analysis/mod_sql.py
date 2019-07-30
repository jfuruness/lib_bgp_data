#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains table sql queries"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Luke Malinowski"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

#########3
# This file has been checked and all indexes are used in queries

total_ann_sql = """SELECT (SELECT count(*) FROM mrt_w_roas) - SUM(total) AS total FROM
                (SELECT count(exir.asn) AS total
                    FROM extrapolation_inverse_results exir
                WHERE exir.asn = 42177 OR exir.asn = 1
                GROUP BY exir.asn) a;"""

_invalid_asn_create_subtables_sql = [
    """SELECT (SELECT COUNT(*)  AS total FROM invalid_asn_blocked_hijacked) - 
(SELECT COALESCE(COUNT(*), 0) AS total FROM (SELECT DISTINCT iabh.prefix, iabh.origin
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_asn_blocked_hijacked iabh
                ON exir.prefix = iabh.prefix AND iabh.origin = exir.origin
            WHERE exir.asn = 1 OR exir.asn = 42177) missed) AS total;"""


"""
SELECT (SELECT COUNT(*)  AS total FROM invalid_asn_blocked_not_hijacked) - 
(SELECT COALESCE(COUNT(*), 0) AS total FROM (SELECT DISTINCT iabnh.prefix, iabnh.origin
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_asn_blocked_not_hijacked iabnh
                ON exir.prefix = iabnh.prefix AND iabnh.origin = exir.origin
            WHERE exir.asn = 1 OR exir.asn = 42177) missed) AS total;"""

    """CREATE TABLE invalid_asn_not_blocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_not_blocked_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_asn_not_blocked_hijacked ianbh
                ON exir.prefix = ianbh.prefix AND ianbh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;"""]
_invalid_asn_subtables_index_sql = [
    """CREATE INDEX ON invalid_asn_blocked_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_asn_blocked_not_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_asn_not_blocked_hijacked_stats(asn);"""]
_invalid_asn_subtables_sql = _invalid_asn_drop_subtables_sql
_invalid_asn_subtables_sql += _invalid_asn_create_subtables_sql
_invalid_asn_subtables_sql +=  _invalid_asn_subtables_index_sql


# invalid_length_subtables_sql
_invalid_length_drop_subtables_sql = [
    """DROP TABLE IF EXISTS invalid_length_blocked_hijacked_stats""",
    """DROP TABLE IF EXISTS invalid_length_blocked_not_hijacked_stats""",
    """DROP TABLE IF EXISTS invalid_length_not_blocked_hijacked_stats"""]
_invalid_length_create_subtables_sql = [
    """CREATE TABLE invalid_length_blocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_length_blocked_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_length_blocked_hijacked ilbh
                ON exir.prefix = ilbh.prefix AND ilbh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;""",
    """CREATE TABLE invalid_length_blocked_not_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*)
                FROM invalid_length_blocked_not_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_length_blocked_not_hijacked ilbnh
                ON exir.prefix = ilbnh.prefix AND ilbnh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;""",
    """CREATE TABLE invalid_length_not_blocked_hijacked_stats AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_length_not_blocked_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_length_not_blocked_hijacked ilnbh
                ON exir.prefix = ilnbh.prefix AND ilnbh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;"""]
_invalid_length_subtables_index_sql = [
    """CREATE INDEX ON invalid_length_blocked_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_length_blocked_not_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_length_not_blocked_hijacked_stats(asn);"""]
_invalid_length_subtables_sql = _invalid_length_drop_subtables_sql
_invalid_length_subtables_sql += _invalid_length_create_subtables_sql
_invalid_length_subtables_sql +=  _invalid_length_subtables_index_sql
 
_invalid_asn_policy_sql = [
    "DROP TABLE IF EXISTS invalid_asn",
    """CREATE TABLE invalid_asn AS SELECT
    asns.asn AS parent_asn,
    iabhs.total AS blocked_hijacked,
    ianbhs.total AS not_blocked_hijacked,
    iabnhs.total AS blocked_not_hijacked,
    asns.total - iabhs.total - ianbhs.total - iabnhs.total
        AS not_blocked_not_hijacked
    FROM total_announcements asns
        LEFT JOIN invalid_asn_blocked_hijacked_stats iabhs
            ON iabhs.asn = asns.asn
        LEFT JOIN invalid_asn_not_blocked_hijacked_stats ianbhs
            ON ianbhs.asn = asns.asn
        LEFT JOIN invalid_asn_blocked_not_hijacked_stats iabnhs
            ON iabnhs.asn = asns.asn;""",
    """CREATE INDEX ON invalid_asn (parent_asn)"""]

_invalid_length_policy_sql = [
    "DROP TABLE IF EXISTS invalid_length",
    """CREATE TABLE invalid_length AS SELECT
    asns.asn AS parent_asn,
    iabhs.total AS blocked_hijacked,
    ianbhs.total AS not_blocked_hijacked,
    iabnhs.total AS blocked_not_hijacked,
    asns.total - iabhs.total - ianbhs.total - iabnhs.total
        AS not_blocked_not_hijacked
    FROM total_announcements asns
        LEFT JOIN invalid_length_blocked_hijacked_stats iabhs
            ON iabhs.asn = asns.asn
        LEFT JOIN invalid_length_not_blocked_hijacked_stats ianbhs
            ON ianbhs.asn = asns.asn
        LEFT JOIN invalid_length_blocked_not_hijacked_stats iabnhs
            ON iabnhs.asn = asns.asn;""",
    """CREATE INDEX ON invalid_length (parent_asn);"""]

_rov_policy_sql = [
    "DROP TABLE IF EXISTS rov",
    """CREATE TABLE rov AS SELECT
    asns.asn AS parent_asn,
    ilp.blocked_hijacked + iap.blocked_hijacked AS blocked_hijacked,
    ilp.not_blocked_hijacked + ilp.blocked_hijacked - iap.blocked_hijacked
        - ilp.blocked_hijacked
        AS not_blocked_hijacked,
    ilp.blocked_not_hijacked + iap.blocked_not_hijacked
        AS blocked_not_hijacked,
    asns.total - ilp.blocked_hijacked - ilp.not_blocked_hijacked
        - ilp.blocked_not_hijacked - iap.blocked_hijacked
        - iap.not_blocked_hijacked - iap.blocked_not_hijacked
            AS not_blocked_not_hijacked
    FROM total_announcements asns
        LEFT JOIN invalid_length ilp ON ilp.parent_asn = asns.asn
        LEFT JOIN invalid_asn iap ON iap.parent_asn = asns.asn;""",
    """CREATE INDEX ON rov (parent_asn);"""]

all_sql_queries = _get_total_announcements_sql + _invalid_asn_subtables_sql
all_sql_queries += _invalid_length_subtables_sql
all_sql_queries += _invalid_asn_policy_sql + _invalid_length_policy_sql
all_sql_queries += _rov_policy_sql
