#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains table sql queries"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


#split_validity_table_sql
_drop_tables = [
    "DROP TABLE IF EXISTS invalid_length_blocked_hijacked",
    "DROP TABLE IF EXISTS invalid_length_blocked_not_hijacked",
    "DROP TABLE IF EXISTS invalid_length_unblocked_hijacked",
    "DROP TABLE IF EXISTS invalid_asn_blocked_hijacked",
    "DROP TABLE IF EXISTS invalid_asn_blocked_not_hijacked",
    "DROP TABLE IF EXISTS invalid_asn_unblocked_hijacked",
    "DROP TABLE IF EXISTS rov_unblocked_hijacked"]
_create_tables = [
    """CREATE UNLOGGED TABLE invalid_length_blocked_not_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    LEFT OUTER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity = -1 AND h.prefix IS NULL and h.origin IS NULL);"""
    """CREATE UNLOGGED TABLE invalid_length_blocked_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity = -1);"""
    """CREATE UNLOGGED TABLE invalid_length_unblocked_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity>=0 OR v.validity=-2);""",
    """CREATE UNLOGGED TABLE invalid_asn_blocked_not_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    LEFT OUTER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity = -2 AND h.prefix IS NULL and h.origin IS NULL);""",
    """CREATE UNLOGGED TABLE invalid_asn_blocked_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity = -2);""",
    """CREATE UNLOGGED TABLE invalid_asn_unblocked_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity>=0 OR v.validity=-1);""",
    """CREATE UNLOGGED TABLE rov_unblocked_hijacked AS
    (SELECT v.prefix, v.asn AS origin FROM rov_validity v
    INNER JOIN hijack_temp h
    ON h.prefix = v.prefix AND h.origin = v.asn
    WHERE v.validity >=0);"""]
_index_tables = [
    """CREATE INDEX ON rov_unblocked_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON rov_unblocked_hijacked
    USING GIST(prefix inet_ops);""",
    """CREATE INDEX ON invalid_asn_blocked_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON invalid_asn_blocked_hijacked
    USING GIST(prefix inet_ops);""",
    """CREATE INDEX ON invalid_asn_blocked_not_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON invalid_asn_blocked_not_hijacked
    USING GIST(prefix inet_ops);""",
    """CREATE INDEX ON invalid_asn_unblocked_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON invalid_asn_unblocked_hijacked
    USING GIST(prefix inet_ops);""",
    """CREATE INDEX ON invalid_length_blocked_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON invalid_length_blocked_hijacked
    USING GIST(prefix inet_ops);""",
    """CREATE INDEX ON invalid_length_blocked_not_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON invalid_length_blocked_not_hijacked
    USING GIST(prefix inet_ops);""",
    """CREATE INDEX ON invalid_length_unblocked_hijacked
    USING GIST(prefix inet_ops, origin);""",
    """CREATE INDEX ON invalid_length_unblocked_hijacked
    USING GIST(prefix inet_ops);"""]

split_validity_table_sql = _drop_tables + _create_tables + _index_tables
