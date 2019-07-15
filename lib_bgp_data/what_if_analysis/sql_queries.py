#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains table sql queries"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Luke Malinowski"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

# I know the lines on this file will be off, it's crazy sql man whatever
_get_total_announcements_sql = [
    """DROP TABLE IF EXISTS total_announcements""",
    """CREATE UNLOGGED TABLE total_announcements  AS
        (SELECT exir.asn, (SELECT count(*) FROM mrt_w_roas) - count(exir.asn)
        AS total FROM extrapolation_inverse_results exir
        GROUP BY exir.asn);""",
    """CREATE INDEX ON total_announcements(asn);"""]
# invalid_asn_subtables_sql\
_invalid_asn_drop_subtables_sql = [
    """DROP TABLE IF EXISTS invalid_asn_blocked_hijacked_stats""",
    """DROP TABLE IF EXISTS invalid_asn_blocked_not_hijacked_stats""",
    """DROP TABLE IF EXISTS invalid_asn_unblocked_hijacked_stats"""]
_invalid_asn_create_subtables_sql = [
    """CREATE TABLE invalid_asn_blocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_blocked_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_asn_blocked_hijacked iabh
                ON exir.prefix = iabh.prefix AND iabh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;""",
    """CREATE TABLE invalid_asn_blocked_not_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_blocked_not_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_asn_blocked_not_hijacked iabnh
                ON exir.prefix = iabnh.prefix AND iabnh.origin = exir.origin
                GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;""",
    """CREATE TABLE invalid_asn_unblocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_unblocked_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_asn_unblocked_hijacked ianbh
                ON exir.prefix = ianbh.prefix AND ianbh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;"""]
_invalid_asn_subtables_index_sql = [
    """CREATE INDEX ON invalid_asn_blocked_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_asn_blocked_not_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_asn_unblocked_hijacked_stats(asn);"""]
_invalid_asn_subtables_sql = _invalid_asn_drop_subtables_sql
_invalid_asn_subtables_sql += _invalid_asn_create_subtables_sql
_invalid_asn_subtables_sql +=  _invalid_asn_subtables_index_sql


# invalid_length_subtables_sql
_invalid_length_drop_subtables_sql = [
    """DROP TABLE IF EXISTS invalid_length_blocked_hijacked_stats""",
    """DROP TABLE IF EXISTS invalid_length_blocked_not_hijacked_stats""",
    """DROP TABLE IF EXISTS invalid_length_unblocked_hijacked_stats"""]
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
    """CREATE TABLE invalid_length_unblocked_hijacked_stats AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_length_unblocked_hijacked)
            - COALESCE(missed.total, 0) AS total FROM total_announcements ta
        LEFT JOIN (
            SELECT exir.asn, COUNT(exir.asn) AS total
                FROM extrapolation_inverse_results exir
            INNER JOIN invalid_length_unblocked_hijacked ilnbh
                ON exir.prefix = ilnbh.prefix AND ilnbh.origin = exir.origin
            GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;"""]
_invalid_length_subtables_index_sql = [
    """CREATE INDEX ON invalid_length_blocked_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_length_blocked_not_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_length_unblocked_hijacked_stats(asn);"""]
_invalid_length_subtables_sql = _invalid_length_drop_subtables_sql
_invalid_length_subtables_sql += _invalid_length_create_subtables_sql
_invalid_length_subtables_sql +=  _invalid_length_subtables_index_sql

_url_table_sql = ["DROP TABLE IF EXISTS urls_list",
                  """CREATE TABLE urls_list AS (SELECT ta.asn, ARRAY_AGG(ht.url)
                     AS urls FROM hijack_temp ht
                 INNER JOIN total_announcements ta
                     ON ht.origin = ta.asn GROUP BY ta.asn);""",
                 """CREATE INDEX ON urls_list(asn)"""]
    
_invalid_asn_policy_sql = [
    "DROP TABLE IF EXISTS invalid_asn_policy",
    """CREATE TABLE invalid_asn_policy AS SELECT
    asns.asn AS asn,
    iabhs.total AS hijack_blocked,
    ianbhs.total AS hijack_not_blocked,
    iabnhs.total AS not_hijacked_blocked,
    asns.total - iabhs.total - ianbhs.total - iabnhs.total
        AS not_hijacked_not_blocked,
    urls.urls,
    stubs.parent_asn
    FROM total_announcements asns
        LEFT JOIN invalid_asn_blocked_hijacked_stats iabhs
            ON iabhs.asn = asns.asn
        LEFT JOIN invalid_asn_unblocked_hijacked_stats ianbhs
            ON ianbhs.asn = asns.asn
        LEFT JOIN invalid_asn_blocked_not_hijacked_stats iabnhs
            ON iabnhs.asn = asns.asn
        LEFT JOIN stubs ON stubs.stub_asn = asns.asn
        LEFT JOIN urls_list urls ON urls.asn = asns.asn;""",
    """CREATE INDEX ON invalid_asn_policy (asn)"""]

_invalid_lenth_policy_sql = [
    "DROP TABLE IF EXISTS invalid_length_policy",
    """CREATE TABLE invalid_length_policy AS SELECT
    asns.asn AS asn,
    iabhs.total AS hijack_blocked,
    ianbhs.total AS hijack_not_blocked,
    iabnhs.total AS not_hijacked_blocked,
    asns.total - iabhs.total - ianbhs.total - iabnhs.total
        AS not_hijacked_not_blocked,
    urls.urls,
    stubs.parent_asn
    FROM total_announcements asns
        LEFT JOIN invalid_length_blocked_hijacked_stats iabhs
            ON iabhs.asn = asns.asn
        LEFT JOIN invalid_length_unblocked_hijacked_stats ianbhs
            ON ianbhs.asn = asns.asn
        LEFT JOIN invalid_length_blocked_not_hijacked_stats iabnhs
            ON iabnhs.asn = asns.asn
        LEFT JOIN stubs ON stubs.stub_asn = asns.asn
        LEFT JOIN urls_list urls ON urls.asn = asns.asn;""",
    """CREATE INDEX ON invalid_length_policy (asn);"""]

_rov_policy_sql = [
    "DROP TABLE IF EXISTS rov_policy",
    """CREATE TABLE rov_policy AS SELECT
    asns.asn AS asn,
    ilp.hijack_blocked + iap.hijack_blocked AS hijacked_blocked,
    ilp.hijack_not_blocked AS hijacked_not_blocked,
    ilp.not_hijacked_blocked + iap.not_hijacked_blocked
        AS not_hijacked_blocked,
    asns.total - ilp.hijack_blocked - ilp.hijack_not_blocked
        - ilp.not_hijacked_blocked,
    urls.urls,
    stubs.parent_asn
    FROM total_announcements asns
        LEFT JOIN invalid_length_policy ilp ON ilp.asn = asns.asn
        LEFT JOIN invalid_asn_policy iap ON iap.asn = asns.asn
        LEFT JOIN stubs ON stubs.stub_asn = asns.asn
        LEFT JOIN urls_list urls ON urls.asn = asns.asn;""",
    """CREATE INDEX ON rov_policy (asn);"""]

all_sql_queries = _get_total_announcements_sql + _invalid_asn_subtables_sql
all_sql_queries += _invalid_length_subtables_sql + _url_table_sql
all_sql_queries += _invalid_asn_policy_sql + _invalid_lenth_policy_sql
all_sql_queries += _rov_policy_sql
