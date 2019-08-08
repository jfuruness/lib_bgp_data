#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains sql queries.

These sql queries permute the hijack table with every possible
combination of blocked or not, and policy. See __init__.py for a more
in depth explanation.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


_drop_tables = [
    "DROP TABLE IF EXISTS invalid_length_blocked_hijacked",
    "DROP TABLE IF EXISTS invalid_length_blocked_not_hijacked",
    "DROP TABLE IF EXISTS invalid_length_not_blocked_hijacked",
    "DROP TABLE IF EXISTS invalid_asn_blocked_hijacked",
    "DROP TABLE IF EXISTS invalid_asn_blocked_not_hijacked",
    "DROP TABLE IF EXISTS invalid_asn_not_blocked_hijacked",
    "DROP TABLE IF EXISTS rov_not_blocked_hijacked"]
_create_tables = [
    """CREATE UNLOGGED TABLE invalid_length_blocked_not_hijacked AS
    (SELECT v.prefix, v.origin FROM rov_validity v
    LEFT OUTER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity = -1 AND h.prefix IS NULL AND h.origin IS NULL);"""
    """CREATE UNLOGGED TABLE invalid_length_blocked_hijacked AS
    (SELECT v.prefix, v.origin, h.url FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity = -1);"""
    """CREATE UNLOGGED TABLE invalid_length_not_blocked_hijacked AS
    (SELECT v.prefix, v.origin, h.url FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity>=0 OR v.validity=-2);""",


    """CREATE UNLOGGED TABLE invalid_asn_blocked_not_hijacked AS
    (SELECT v.prefix, v.origin FROM rov_validity v
    LEFT OUTER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity = -2 AND h.prefix IS NULL and h.origin IS NULL);""",
    """CREATE UNLOGGED TABLE invalid_asn_blocked_hijacked AS
    (SELECT v.prefix, v.origin, h.url FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity = -2);""",
    """CREATE UNLOGGED TABLE invalid_asn_not_blocked_hijacked AS
    (SELECT v.prefix, v.origin, h.url FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity>=-1);""",
    """CREATE UNLOGGED TABLE rov_not_blocked_hijacked AS
    (SELECT v.prefix, v.origin, h.url FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.origin
    WHERE v.validity >=0);"""]

split_validity_table_sql = _drop_tables + _create_tables
