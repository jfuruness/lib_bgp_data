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
get_total_announcements_sql = [
    """CREATE UNLOGGED TABLE total_announcements AS
           (SELECT exir.asn,
            (SELECT count(DISTINCT prefix) FROM mrt_w_roas)
                - count(exir.asn)
            AS total FROM extrapolation_inverse_results exir
            GROUP BY exir.asn);
    """,
    """CREATE INDEX ON total_announcements USING asn;""",        
##########ABOVE WORKS REFACTOR DOES NOT
    # Now we have all of our tables that we need to calculate the statistics
    """CREATE TABLE invalid_asn_hijacked_stats AS
       SELECT ta.asn AS asn, COUNT(ta.asn) AS TOTAL FROM (invalid_asn_hijacked
        LEFT JOIN
        (SELECT exir.asn, exir.prefix, exir.origin FROM extrapolation_inverse_results exir
        LEFT JOIN invalid_asn_hijacked iah ON exir.prefix = iah.prefix) for_index
        ON invalid_asn_hijacked.origin = for_index.origin) total_announcements ta
       GROUP BY ta.asn;
    """,
    
    """CREATE TABLE invalid_asn_not_hijacked_stats AS
       SELECT exir.asn, COUNT(exir.asn) AS TOTAL FROM
       invalid_asn_not_hijacked iah LEFT JOIN extrapolation_inverse_results exir
       ON iah.prefix = exir.prefix;
    """,
    """CREATE INDEX ON invalid_asn_hijacked_stats USING asn;""",
    """CREATE INDEX ON invalid_asn_not_hijacked_stats USING asn;""",
    
    
    """CREATE TABLE invalid_length_hijacked_stats AS
       SELECT final_table.asn AS asn, COUNT(final_table.asn) AS TOTAL FROM (invalid_length_hijacked
        LEFT JOIN
        (SELECT exir.asn, exir.prefix, exir.origin FROM extrapolation_inverse_results exir
        LEFT JOIN invalid_length_hijacked ilh ON exir.prefix = ilh.prefix) for_index
        ON invalid_length_hijacked.origin = for_index.origin) final_table
       GROUP BY final_table.asn;
    """,
    
    """CREATE TABLE invalid_length_not_hijacked_stats AS
       SELECT exir.asn, COUNT(exir.asn) AS TOTAL FROM
       invalid_length_not_hijacked ilh LEFT JOIN extrapolation_inverse_results exir
       ON ilh.prefix = exir.prefix;
    """,
    """CREATE INDEX ON invalid_length_hijacked_stats USING asn;""",
    """CREATE INDEX ON invalid_length_not_hijacked_stats USING asn;""",
    
    """CREATE TABLE unblocked_hijacked_stats AS
       SELECT final_table.asn AS asn, COUNT(final_table.asn) AS TOTAL FROM (unblocked_hijacked uh
        LEFT JOIN
        (SELECT exir.asn, exir.prefix, exir.origin FROM extrapolation_inverse_results exir
        LEFT JOIN unblocked_hijacked uh ON exir.prefix = uh.prefix) for_index
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
