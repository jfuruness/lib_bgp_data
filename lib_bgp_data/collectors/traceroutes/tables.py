#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from ...utils.database import Generic_Table


class ROAs_Table(Generic_Table):
    """Announcements table class"""

    __slots__ = []

    name = "roas"
    columns = ["asn", "prefix", "max_length", "created_at"]

    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS roas (
              asn bigint,
              prefix cidr,
              max_length integer,
              created_at bigint
              ) ;"""
        self.execute(sql)

    def create_index(self):
        """Creates a bunch of indexes to be used on the table"""

        logging.debug("Creating index on roas")
        sql = """CREATE INDEX IF NOT EXISTS roas_index
              ON roas USING GIST(prefix inet_ops)"""
        self.execute(sql)
