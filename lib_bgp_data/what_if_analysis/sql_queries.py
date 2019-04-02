#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains table sql queries"""

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

policy_2_sql_queries = [

]
# Step 0: split up the validity table, and create indexes on all of them
# We do this because we split them up multiple times in our queries,
# And this way we only split them once, and then have the index
# If I really felt like it I'm sure theres a way to combine this
# all into one massive query but whatever
"""CREATE TABLE validity_unblocked AS
       (SELECT v.prefix, v.asn AS origin FROM validity v
       WHERE v.validity >= 0);
"""
#invalid length
"""CREATE TABLE validity_invalid_length AS
       (SELECT v.prefix, v.asn AS origin FROM validity v
       WHERE v.validity = -1);
"""
#invalid asn
"""CREATE TABLE validity_invalid_asn AS
       (SELECT v.prefix, v.asn AS origin FROM validity v
       WHERE v.validity = -2);
"""
# Then create indexes and drop the tables
"""CREATE INDEX ON validity_unblocked
   USING GIST (prefix inet_ops, origin);
"""
"""CREATE INDEX ON validity_invalid_length
   USING GIST (prefix inet_ops, origin);
"""
"""CREATE INDEX ON validity_invalid_asn
   USING GIST (prefix inet_ops, origin);
"""

# The next thing is that the intersection between hijack data
# and extrapolation results occurs in every query.
# So we make those tables and index them
"""CREATE TABLE hijack_temp AS
       (SELECT h.more_specific_prefix AS prefix, h.detected_origin_number AS origin, h.url
       FROM hijack h
       WHERE
           (h.start_time, COALESCE(h.end_time, current_time)) OVERLAPS
           (%s, %s)
       ),
"""
"""CREATE INDEX ON hijack_temp USING GIST (prefix inet_ops, origin)"""
"""CREATE TABLE hijacked_extrapolation_results_temp AS
       (SELECT exr.asn, h.prefix, h.origin, h.url FROM hijack_temp h
        INNER JOIN extrapolation_results exr ON
            h.prefix = exr.prefix AND h.origin = exr.origin);
"""
"""CREATE INDEX ON hijacked_extrapolation_results_temp
   USING GIST (prefix inet_ops, origin)
"""
"""CREATE TABLE not_hijacked_extrapolation_results_temp AS
       (SELECT exr.asn, h.prefix, h.origin, h.url FROM hijack_temp h
        RIGHT JOIN extrapolation_results exr ON
            h.prefix = exr.prefix AND h.origin = exr.origin
            WHERE h.prefix IS NULL);
"""
"""CREATE INDEX ON not_hijacked_extrapolation_results_temp
   USING GIST (prefix inet_ops, origin);
"""

# Step 2: get the four temporary tables
# List of asns not unique invalid asn hijacked and blocked
"""WITH iahb_tmp AS (SELECT hexr.asn, hexr.url
      FROM validity_invalid_asn via
      INNER JOIN hijacked_extrapolation_results hexr ON
          hexr.prefix = via.prefix AND hexr.origin = via.origin,
"""
# List of asns not unique invalid_asn hijacked and not blocked
"""WITH iahnb_tmp AS (SELECT hexr.asn, hexr.url
       FROM validity_unblocked vu
       INNER JOIN hijacked_extrapolation_results hexr ON
           hexr.prefix = vu.prefix AND hexr.origin = vu.origin,
"""
# List of asns not unique invalid_asn not hijacked and blocked
"""WITH ianhb_tmp AS (SELECT nhexr.asn, nhexr.url
       FROM validity_invalid_asn via
       INNER JOIN not_hijacked_extrapolation_results nhexr ON
           nhexr.prefix = via.prefix AND nhexr.origin = via.origin,
"""
# List of asns not unique invalid_asn not hijacked and not blocked
"""WITH ianhnb_tmp AS (SELECT nhexr.asn, nhexr.url
       FROM validity_unblocked vu
       INNER JOIN not_hijacked_extrapolation_results nhexr ON
           nhexr.prefix = vu.prefix AND nhexr.origin = vu.origin,
"""
# NOTE: Make sure validity has an index on the asn
# Create the policy 2 table with lots of subqueries



#########
########
#########MUST CHANGE SOME OF THESE LEFT JOINS TO SOMETHING ELSE!!!!!
"""CREATE TABLE policy_2 AS SELECT 
       v.asn as asn,
       ia_hb.total AS hijack_blocked,
       hnb.total AS hijack_not_blocked,
       nhb.total AS not_hijacked_blocked,
       nhnb.total as not_hijacked_not_blocked,
       urls.url_list
       FROM validity v
           LEFT JOIN (SELECT ia_hbd.asn, count(*) AS total
                      FROM ia_hb_tmp
                      LEFT JOIN (
                                 SELECT DISTINCT *
                                 FROM ia_hb_tmp
                                ) ia_hbd
                      ON ia_hbd.asn = ia_hb_tmp.asn
                          GROUP BY ia_hbd.asn) ia_hb
               ON ia_hb.asn = v.asn

           LEFT JOIN (SELECT ia_hnbd.asn, count(*) AS total
                 FROM ia_hnb_tmp
                 LEFT JOIN (
                            SELECT DISTINCT *
                            FROM ia_hnb_tmp
                           ) ia_hnbd
                 ON ia_hnbd.asn = ia_hnb_tmp.asn
                     GROUP BY hnbd.asn) ia_hnb
                ON ia_hnb.asn = v.asn

           LEFT JOIN (SELECT ia_nhbd.asn, count(*) AS total
                 FROM ia_nhb_tmp
                 LEFT JOIN (
                            SELECT DISTINCT *
                            FROM ia_nhb_tmp
                           ) ia_nhbd
                 ON ia_nhbd.asn = ia_nhb_tmp.asn
                     GROUP BY ia_nhbd.asn) ia_nhb
                ON ia_nhb.asn = v.asn

           LEFT JOIN (get total announcements from hijacked and not hijacked extrap results and subtract other tables) ia_nhnb
                ON ia_nhnb = v.asn

           LEFT JOIN
               (SELECT ARRAY(SELECT url FROM hijack_temp ht
                             INNER JOIN validity v ON
                                 ht.origin = v.asn) AS url_list) urls
"""
