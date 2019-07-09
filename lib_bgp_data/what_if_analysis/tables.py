#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables classes to store roas"""

import os
import gzip
from psycopg2.extras import RealDictCursor
from ..utils import error_catcher, Database

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Validity_Table(Database):
    """Announcements table class"""

    __slots__ = []

    @error_catcher()
    def __init__(self, logger, cursor_factory=RealDictCursor, test=False):
        """Initializes the announcement table"""

        Database.__init__(self, logger, cursor_factory, test)

    @error_catcher()
    def _create_tables(self):
        """ Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS validity (
                 asn bigint,
                 prefix cidr,
                 validity smallint);"""
        self.cursor.execute(sql)

    @error_catcher()
    def create_index(self):
        """Creates index on validity_table"""

        sql = """CREATE INDEX IF NOT EXISTS validity_valid_index ON validity
                  (validity);"""
        self.cursor.execute(sql)


    @property
    def name(self):
        """Returns the name of the table"""

        return "validity"

    @property
    def columns(self):
        """Returns the columns of the table"""

        return ['asn', 'prefix', 'validity']

    def split_table(self):
        """Splits the table into three based on validity"""

        self.logger.info("Dropping old tables")
        sqls = ["DROP TABLE IF EXISTS invalid_length_blocked_hijacked",
                "DROP TABLE IF EXISTS invalid_length_blocked_not_hijacked",
                "DROP TABLE IF EXISTS invalid_length_unblocked_hijacked",
                "DROP TABLE IF EXISTS invalid_asn_blocked_hijacked",
                "DROP TABLE IF EXISTS invalid_asn_blocked_not_hijacked",
                "DROP TABLE IF EXISTS invalid_asn_unblocked_hijacked",
                "DROP TABLE IF EXISTS rov_unblocked_hijacked"]
        for sql in sqls:
            self.cursor.execute(sql)
        self.logger.info("Creating tables used for what if analysis")
        # Yes I know we could do this all in parallel, but there
        # really is no need since this is fast
        sqls = ["""CREATE UNLOGGED TABLE invalid_length_blocked_not_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                 LEFT OUTER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity = -1 AND h.prefix IS NULL and h.origin IS NULL);
                """,
                """CREATE UNLOGGED TABLE invalid_length_blocked_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                INNER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity = -1);
                """,
                """CREATE UNLOGGED TABLE invalid_length_unblocked_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                INNER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity>=0 OR v.validity=-2);
                """,

                """CREATE UNLOGGED TABLE invalid_asn_blocked_not_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                 LEFT OUTER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity = -2 AND h.prefix IS NULL and h.origin IS NULL);
                """,
                """CREATE UNLOGGED TABLE invalid_asn_blocked_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                INNER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity = -2);
                """,
                """CREATE UNLOGGED TABLE invalid_asn_unblocked_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                INNER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity>=0 OR v.validity=-1);
                """,

                """CREATE UNLOGGED TABLE rov_unblocked_hijacked AS
                (SELECT v.prefix, v.asn AS origin FROM validity v
                INNER JOIN hijack_temp h
                ON h.prefix = v.prefix AND h.origin = v.asn
                WHERE v.validity >=0);
                """,
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
                USING GIST(prefix inet_ops);"""

                """CREATE INDEX ON invalid_length_unblocked_hijacked
                USING GIST(prefix inet_ops, origin);""",
                """CREATE INDEX ON invalid_length_unblocked_hijacked
                USING GIST(prefix inet_ops);"""
                ]
        for sql in sqls:
            self.cursor.execute(sql)
