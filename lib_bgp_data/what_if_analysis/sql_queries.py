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
    """CREATE UNLOGGED TABLE total_announcements  AS
           (SELECT exir.asn,
            (SELECT count(*) FROM mrt_w_roas)
                - count(exir.asn)
            AS total FROM extrapolation_inverse_results exir
            GROUP BY exir.asn);
    """,
    """CREATE INDEX ON total_announcements(asn);""",        
##########ABOVE WORKS REFACTOR DOES NOT
    # Now we have all of our tables that we need to calculate the statistics
    """CREATE TABLE invalid_asn_blocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_blocked_hijacked) - COALESCE(missed.total, 0) AS total 
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN invalid_asn_blocked_hijacked iabh ON exir.prefix = iabh.prefix AND iabh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE TABLE invalid_asn_blocked_not_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_blocked_not_hijacked) - COALESCE(missed.total, 0) AS total 
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN invalid_asn_blocked_not_hijacked iabnh ON exir.prefix = iabnh.prefix AND iabnh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE TABLE invalid_asn_unblocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_asn_unblocked_hijacked) - COALESCE(missed.total, 0) AS total
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN invalid_asn_unblocked_hijacked ianbh ON exir.prefix = ianbh.prefix AND ianbh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE INDEX ON invalid_asn_blocked_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_asn_blocked_not_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_asn_unblocked_hijacked_stats(asn);""",
    
    """CREATE TABLE invalid_length_blocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_length_blocked_hijacked) - COALESCE(missed.total, 0) AS total 
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN invalid_length_blocked_hijacked ilbh ON exir.prefix = ilbh.prefix AND ilbh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE TABLE invalid_length_blocked_not_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_length_blocked_not_hijacked) - COALESCE(missed.total, 0) AS total 
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN invalid_length_blocked_not_hijacked ilbnh ON exir.prefix = ilbnh.prefix AND ilbnh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE TABLE invalid_length_unblocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM invalid_length_unblocked_hijacked) - COALESCE(missed.total, 0) AS total
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN invalid_length_unblocked_hijacked ilnbh ON exir.prefix = ilnbh.prefix AND ilnbh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE INDEX ON invalid_length_blocked_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_length_blocked_not_hijacked_stats(asn);""",
    """CREATE INDEX ON invalid_length_unblocked_hijacked_stats(asn);""",



    """CREATE TABLE rov_unblocked_hijacked_stats  AS
        SELECT ta.asn, (SELECT COUNT(*) FROM rov_unblocked_hijacked) - COALESCE(missed.total, 0) AS total
        FROM total_announcements ta LEFT JOIN (SELECT exir.asn, COUNT(exir.asn) AS total FROM extrapolation_inverse_results exir
        INNER JOIN rov_unblocked_hijacked rovnbh ON exir.prefix = rovnbh.prefix AND rovnbh.origin = exir.origin GROUP BY exir.asn) missed
        ON ta.asn = missed.asn;
    """,

    """CREATE INDEX ON rov_unblocked_hijacked_stats(asn);""",
 
    """CREATE TABLE urls_list  AS (SELECT ta.asn, ARRAY_AGG(ht.url) AS urls FROM hijack_temp ht
                                 INNER JOIN total_announcements ta ON
                                     ht.origin = ta.asn GROUP BY ta.asn);""", 
    
    
    
    """CREATE TABLE invalid_asn_policy AS SELECT
           asns.asn AS asn,
           iabhs.total AS hijack_blocked,
           ianbhs.total AS hijack_not_blocked,
           iabnhs.total AS not_hijacked_blocked,
           asns.total - iabhs.total - ianbhs.total - iabnhs.total AS not_hijacked_not_blocked
           FROM total_announcements asns
               LEFT JOIN invalid_asn_blocked_hijacked_stats iabhs ON iabhs.asn = asns.asn
               LEFT JOIN invalid_asn_unblocked_hijacked_stats ianbhs ON ianbhs.asn = asns.asn
               LEFT JOIN invalid_asn_blocked_not_hijacked_stats iabnhs ON iabnhs.asn = asns.asn;
    """,
    """CREATE INDEX ON invalid_asn_policy USING asn""",


    """CREATE TABLE invalid_length_policy AS SELECT
           asns.asn AS asn,
           iabhs.total AS hijack_blocked,
           ianbhs.total AS hijack_not_blocked,
           iabnhs.total AS not_hijacked_blocked,
           asns.total - iabhs.total - ianbhs.total - iabnhs.total AS not_hijacked_not_blocked
           FROM total_announcements asns
               LEFT JOIN invalid_length_blocked_hijacked_stats iabhs ON iabhs.asn = asns.asn
               LEFT JOIN invalid_length_unblocked_hijacked_stats ianbhs ON ianbhs.asn = asns.asn
               LEFT JOIN invalid_length_blocked_not_hijacked_stats iabnhs ON iabnhs.asn = asns.asn;
    """,
    """CREATE INDEX ON invalid_length_policy USING asn""",




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
