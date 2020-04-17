#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class Input_Subtables

These subtables act as input to the extrapolator

In depth explanation in README
"""


__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from ..relationships_parser.tables import ASes_Table

class Input_Subtables:
    """Contains subtable functionality for pre exr functions"""

    def set_adopting_ases(self, percent, attacker):
        for subtable in self.tables:
            subtable.set_adopting_ases(percent, attacker)

class Input_Subtable:
    """Subtable class for ease of use"""

    def set_adopting_ases(self, percent, attacker):
        maybe_adopters = len(self.ases) - (1 if attacker in self.ases else 0)
        num_adopters = maybe_adopters * percent // 100
        sql = f"""WITH adopting_ases AS (
                  SELECT asn, TRUE AS val FROM {self.Input_Table.name} a WHERE a.asn != {attacker}
                  ORDER BY RANDOM() LIMIT {num_adopters})
                UPDATE {ASes_Table.name}
                    SET as_types = array_append(as_types, e.val)
                FROM (SELECT b.asn, COALESCE(c.val, FALSE) AS val FROM {self.Input_Table.name} b
                    LEFT JOIN adopting_ases c ON c.asn = b.asn) e
                WHERE e.asn = {ASes_Table.name}.asn;"""
        self.Input_Table.execute(sql)
