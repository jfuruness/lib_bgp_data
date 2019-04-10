#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains table sql queries"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Luke Malinowski"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

# I know the lines on this file will be off, it's crazy sql man whatever

# Before the validator is run we can start doing this on the extrapolation results:
get_hijack_temp_sql = [
    """CREATE UNLOGGED TABLE hijack_temp AS
        (SELECT h.more_specific_prefix AS prefix, h.detected_origin_number AS origin, h.url
        FROM hijack h
        WHERE
            (h.start_time, COALESCE(h.end_time, now()::timestamp)) OVERLAPS
            (%s, %s)
        );
     """,
     """CREATE INDEX ON hijack_temp USING GIST (prefix inet_ops, origin);""",
     """CREATE INDEX ON hijack_temp USING GIST (prefix inet_ops);"""
    ]
get_total_announcements_sql = [
    """CREATE UNLOGGED TABLE total_announcements AS
           (SELECT exr.asn, count(exr.asn) AS total FROM extrapolation_results exr
            GROUP BY exr.asn);
    """,
    """CREATE INDEX ON total_announcements USING asn;"""
    ]
run_after_extrapolator_sql = get_hijack_temp_sql + get_total_announcements_sql

# Then, validator is run. We now have validity table. Run this query asynchronously:
validity_parallel_split = [
    ["""CREATE UNLOGGED TABLE unblocked AS
           (SELECT v.prefix, v.asn AS origin FROM validity v
           WHERE v.validity >= 0);
     """,
    """CREATE UNLOGGED TABLE invalid_asn AS
           (SELECT v.prefix, v.asn AS origin FROM validity v
           WHERE v.validity = -2);
    """,
    """CREATE UNLOGGED TABLE invalid_length AS
           (SELECT v.prefix, v.asn AS origin FROM validity v
           WHERE v.validity = -1);
    """, 
    """CREATE INDEX CONCURRENTLY ON unblocked USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX CONCURRENTLY ON unblocked USING GIST(prefix inet_ops);""",
    """CREATE INDEX CONCURRENTLY ON invalid_asn USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX CONCURRENTLY ON invalid_asn USING GIST(prefix inet_ops);""",
    """CREATE INDEX CONCURRENTLY ON invalid_length USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX CONCURRENTLY ON invalid_length USING GIST(prefix inet_ops);""",
    ]
    run_after_validity_split = [
    """CREATE UNLOGGED TABLE unblocked_hijacked AS
           (SELECT u.prefix, u.origin FROM unblocked u
            LEFT JOIN hijack_temp h ON h.prefix = u.prefix AND h.origin = u.origin;
    """,
    """CREATE INDEX CONCURRENTLY ON unblocked_hijack USING (prefix inet_ops);""",
    
    
    
    """CREATE UNLOGGED TABLE invalid_asn_hijacked AS
           (SELECT ia.prefix, ia.origin FROM invalid_asn ia
            LEFT JOIN hijack_temp h ON h.prefix = ia.prefix AND h.origin = ia.origin;
    """,
    """CREATE UNLOGGED TABLE invalid_asn_not_hijacked AS
           (SELECT ia.prefix, ia.origin FROM invalid_asn ia
            LEFT JOIN hijack_temp h ON h.prefix = ia.prefix
            WHERE h.prefix IS NULL;
    """,
    """CREATE INDEX CONCURRENTLY ON invalid_asn_hijacked USING (prefix inet_ops);""",
    """CREATE INDEX CONCURRENTLY ON invalid_asn_hijacked USING origin;""",
    """CREATE INDEX CONCURRENTLY ON invalid_asn_not_hijacked USING (prefix inet_ops);""",
    
    
    
    """CREATE UNLOGGED TABLE invalid_length_hijacked AS
           (SELECT il.prefix, il.origin FROM invalid_length il
            LEFT JOIN hijack_temp h ON h.prefix = il.prefix AND h.origin = il.origin;
    """,
    """CREATE UNLOGGED TABLE invalid_length_not_hijacked AS
           (SELECT il.prefix, il.origin FROM invalid_length il
            LEFT JOIN hijack_temp h ON h.prefix = il.prefix
            WHERE h.prefix IS NULL;
    """,
    """CREATE INDEX CONCURRENTLY ON invalid_length_hijacked USING (prefix inet_ops);""",
    """CREATE INDEX CONCURRENTLY ON invalid_length_hijacked USING origin;""",
    """CREATE INDEX CONCURRENTLY ON invalid_length_not_hijacked USING (prefix inet_ops);""",
    ]
    
    """CREATE UNLOGGED TABLE total_announcements AS
           (SELECT exr.asn, count(exr.asn) AS total FROM extrapolation_results exr
            GROUP BY exr.asn);
    """,
    """CREATE INDEX CONCURRENTLY ON total_announcements USING asn;""",
    
    
    
    # Now we have all of our tables that we need to calculate the statistics
    """CREATE TABLE invalid_asn_hijacked_stats AS
       SELECT final_table.asn AS asn, COUNT(final_table.asn) AS TOTAL FROM (invalid_asn_hijacked
        LEFT JOIN
        (SELECT exr.asn, exr.prefix, exr.origin FROM extrapolation_results exr
        LEFT JOIN invalid_asn_hijacked iah ON exr.prefix = iah.prefix) for_index
        ON invalid_asn_hijacked.origin = for_index.origin) final_table
       GROUP BY final_table.asn;
    """,
    
    """CREATE TABLE invalid_asn_not_hijacked_stats AS
       SELECT exr.asn, COUNT(exr.asn) AS TOTAL FROM
       invalid_asn_not_hijacked iah LEFT JOIN extrapolation_results exr
       ON iah.prefix = exr.prefix;
    """,
    """CREATE INDEX ON invalid_asn_hijacked_stats USING asn;""",
    """CREATE INDEX ON invalid_asn_not_hijacked_stats USING asn;""",
    
    
    """CREATE TABLE invalid_length_hijacked_stats AS
       SELECT final_table.asn AS asn, COUNT(final_table.asn) AS TOTAL FROM (invalid_length_hijacked
        LEFT JOIN
        (SELECT exr.asn, exr.prefix, exr.origin FROM extrapolation_results exr
        LEFT JOIN invalid_length_hijacked ilh ON exr.prefix = ilh.prefix) for_index
        ON invalid_length_hijacked.origin = for_index.origin) final_table
       GROUP BY final_table.asn;
    """,
    
    """CREATE TABLE invalid_length_not_hijacked_stats AS
       SELECT exr.asn, COUNT(exr.asn) AS TOTAL FROM
       invalid_length_not_hijacked ilh LEFT JOIN extrapolation_results exr
       ON ilh.prefix = exr.prefix;
    """,
    """CREATE INDEX ON invalid_length_hijacked_stats USING asn;""",
    """CREATE INDEX ON invalid_length_not_hijacked_stats USING asn;""",
    
    """CREATE TABLE unblocked_hijacked_stats AS
       SELECT final_table.asn AS asn, COUNT(final_table.asn) AS TOTAL FROM (unblocked_hijacked uh
        LEFT JOIN
        (SELECT exr.asn, exr.prefix, exr.origin FROM extrapolation_results exr
        LEFT JOIN unblocked_hijacked uh ON exr.prefix = uh.prefix) for_index
        ON uh.origin = for_index.origin) final_table
       GROUP BY final_table.asn;
    """,
    """CREATE INDEX ON unblocked_hijacked_stats USING asn;""",
    
    """CREATE TABLE urls_list AS (SELECT ARRAY(SELECT url FROM hijack_temp ht
                                 INNER JOIN total_announcements ta ON
                                     ht.origin = ta.asn) AS url_list);""",
    
    
    
    
    
    """CREATE TABLE invalid_asn_policy AS SELECT
           asns.asn AS asn,
           iahs.total AS hijack_blocked,
           uhs.total AS hijack_not_blocked,
           ianhs.total AS not_hijacked_blocked,
           asns.total - iahs.total - uhs.total - ianhs.total AS not_hijacked_not_blocked,
           urls.url_list
           FROM total_announcements asns
               LEFT JOIN FROM invalid_asn_hijacked_stats iahs ON iahs.asn = asns.asn
               LEFT JOIN FROM unblocked_hijacked_stats ON uhs.asn = asns.asn
               LEFT JOIN FROM invalid_asn_not_hijacked_stats ianhs ON ianhs.asn = asns.asn
               LEFT JOIN urls_list ON urls_list.asn = asns.asn;
    """,
    """CREATE INDEX ON invalid_asn_policy USING asn""",
    """CREATE TABLE invalid_length_policy AS SELECT
           asns.asn AS asn,
           ilhs.total AS hijack_blocked,
           uhs.total AS hijack_not_blocked,
           ilnhs.total AS not_hijacked_blocked,
           asns.total - ilhs.total - uhs.total - ilnhs.total AS not_hijacked_not_blocked,
           urls.url_list AS urls
           FROM total_announcements asns
               LEFT JOIN FROM invalid_length_hijacked_stats ilhs ON ilhs.asn = asns.asn
               LEFT JOIN FROM unblocked_hijacked_stats ON uhs.asn = asns.asn
               LEFT JOIN FROM invalid_length_not_hijacked_stats ilnhs ON ilnhs.asn = asns.asn
               LEFT JOIN urls_list ON urls_list.asn = asns.asn;
    """,
    """CREATE INDEX ON invalid_length_policy USING asn""",
    """CREATE TABLE rov_policy AS SELECT
           asns.asn AS asn,
           ilp.hijacked_blocked + iap.hijacked_blocked AS hijacked_blocked,
           ilp.hijacked_not_blocked AS hijacked_not_blocked,
           ilp.not_hijacked_blocked + iap.not_hijacked_blocked AS not_hijacked_blocked,
           asns.total - hijacked_blocked - hijacked_not_blocked - not_hijacked_blocked,
           urls.urls_list AS urls
            FROM total_announcements asns
                LEFT JOIN FROM invalid_length_policy ilp ON ilp.asn = asns.asn
                LEFT JOIN FROM invalid_asn_policy iap ON iap.asn = asns.asn
                LEFT JOIN FROM urls ON urls.asn = asns.asn;
    """,
    """CREATE INDEX ON rov_policy USING asn;"""]
