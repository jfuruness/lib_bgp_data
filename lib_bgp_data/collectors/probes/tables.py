#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from ...utils.database import Generic_Table


class Probes_Table(Generic_Table):
    """Probes table class"""

    name = "probes"
    columns = ["probe_id", "asn", "country", "connected", "prefix", "public",
               "address_v4", "anchor"]

    def _create_tables(self):
        """Creates tables if they do not exist"""

        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
              probe_id bigint,
              asn BIGINT,
              country CHAR(2),
              connected BOOLEAN,
              prefix CIDR,
              public BOOLEAN,
              address_v4 INET,
              anchor BOOLEAN
              );"""
        self.execute(sql)
