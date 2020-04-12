#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class Data_Point.

This class is used for gathering all data for a specific percent adoption,
for all possible attacks. See README for in depth instruction
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .enums import Attack_Types, Non_Default_Policies
from .tables import Hijack_Table
from .test import Test


class Data_Point:
    def __init__(self, subtables, percent_iter, percent):
        self.subtables = subtables
        self.percent_iter = percent_iter
        self.percent = percent

    def get_data(self, seeded, exr_bash, exr_kwargs, pbars):
        for test in self.get_possible_tests(seeded=seeded):
            test.run(self.subtables, exr_bash, exr_kwargs, self.percent, pbars)

    def get_possible_tests(self, set_up=True):
        for attack_type in Attack_Types.__members__.values():
            # Sets adopting ases, returns hijack
            attack = self.set_up_test(scenario) if set_up else None

            for adopt_pol in Non_Default_Policies.__members__.values():
                yield Test(attack_type, attack, adopt_pol)

    def set_up_test(self, attack):
        # Fills the hijack table
        with Hijack_Table(clear=True) as db:
            hijack = db.fill_table(self.tables.possible_hijackers, attack)
        # Sets the adopting ases
        self.tables.set_adopting_ases(self.percent_iter, hijack.attacker_asn)
        # Return the hijack class
        return hijack
