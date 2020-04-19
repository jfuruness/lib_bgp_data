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
import os
from random import random

from ..relationships_parser.tables import ASes_Table
from ..utils import utils

class Input_Subtables:
    """Contains subtable functionality for pre exr functions"""

    def set_adopting_ases(self, percent, attacker):
        for subtable in self.tables:
            subtable.set_adopting_ases(percent, attacker)

    def write_to_postgres(self, mp_dps, csv_dir):
        for subtable in self.tables:
            subtable.write_to_postgres(mp_dps, csv_dir)

class Input_Subtable:
    """Subtable class for ease of use"""

    def set_adopting_ases(self, percent, attacker):
        maybe_adopters = len(self.ases) - (1 if attacker in self.ases else 0)
        num_adopters = maybe_adopters * percent // 100
        new_percent = num_adopters / maybe_adopters
        for _as, as_types in self.ases.items():
            as_types.append(random() < new_percent and _as != attacker)

    def extend_ases(self, ases_dict):
        for _as, as_types in ases_dict.items():
            self.ases[_as].extend(as_types)

    def write_to_postgres(self, mp_dps, csv_dir):
        print("Writing")

        self.ases = {x: "{" for x in self.ases}
        mp_dicts = []
        for x in mp_dps:
            mp_dicts.append(x[self.Input_Table.name])
        for _as in self.ases:
            for mp_ases_dict in mp_dicts:
                self.ases[_as] += mp_ases_dict[_as] + ","
        rows = [[k, v[:-1] + "}"] for k, v in self.ases.items()]
        csv_path = os.path.join(csv_dir, f"{self.Input_Table.name}.csv")
        utils.rows_to_db(rows, csv_path, self.Input_Table.__class__)
