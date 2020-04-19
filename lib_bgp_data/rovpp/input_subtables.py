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
        maybe_adopters = len(self.set_ases) - (1 if attacker in self.set_ases else 0)
        num_adopters = maybe_adopters * percent // 100
        new_percent = num_adopters / maybe_adopters
        for _as in self.set_ases:
            self.ases[_as].append(random() < new_percent and _as != attacker)

    def write_to_postgres(self, mp_dps, csv_dir):
        print("Writing")

#        self.ases = {x: "{" for x in self.ases}
#        mp_dicts = []
#        for x in mp_dps:
#            mp_dicts.append(x[self.Input_Table.name])
#        for _as in self.ases:
#            for mp_ases_dict in mp_dicts:
#                self.ases[_as] += mp_ases_dict[_as] + ","
#        rows = [[k, v[:-1] + "}"] for k, v in self.ases.items()]

        csv_path = os.path.join(csv_dir, f"{self.Input_Table.name}.csv")

        rows = self.test(mp_dps, csv_dir)
#        utils.rows_to_db(rows, csv_path, self.Input_Table.__class__)

    # https://stackoverflow.com/a/54802737/8903959
    def split(self, l, n):
        """Yield n number of sequential chunks from l."""
        d, r = divmod(len(l), n)
        for i in range(n):
            si = (d+1)*(i if i < r else r) + d*(0 if i < r else i - r)
            yield l[si:si+(d+1 if i < r else d)]

    def test(self, mp_dps, csv_dir):
        rows = []
        mp_vals = []
        for x in mp_dps:
            mp_vals.append(x[self.Input_Table.name])
        new_vals = list(zip(*mp_vals))
        split_amnt = 18 if "100" not in self.Input_Table.name else 1
        new_vals_chunks = list(self.split(new_vals, split_amnt))
        with ProcessPoolExecutor(max_workers=split_amnt) as executor:
            list(executor.map(write, new_vals_chunks, [os.path.join(csv_dir,f"{x}.csv") for x in range(len(new_vals_chunks))], [self.Input_Table.__class__] * len(new_vals_chunks)))

def write(new_vals, csv_path, table_class):
    rows = [[vals[0][0], "{" + ",".join(list(x[1] for x in vals)) + "}"]
            for vals in new_vals]
    utils.rows_to_db(rows, csv_path, table_class, clear_table=False)

from multiprocessing import cpu_count
from ..database import Database
from concurrent.futures import ProcessPoolExecutor
