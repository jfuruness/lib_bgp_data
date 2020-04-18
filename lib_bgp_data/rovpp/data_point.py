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

from os.path import join
from random import sample

from .attack import Attack, Attack_Generator
from .enums import Attack_Types, Non_Default_Policies
from .tables import Attackers_Table, Victims_Table
from .test import Test

from ..base_classes import Parser
from ..utils import utils

class Data_Point(Parser):

    def __init__(self, subtables, percent_iter, percent):
        self.tables = subtables
        self.percent_iter = percent_iter
        self.percent = percent
        self.tests = []

    def get_possible_tests(self, attack_types, policies, attack_generator):

        for attack_type in attack_types:
            # Attacker victim same across all policy adoptions
            attacker, victim = sample(self.tables.possible_attackers, k=2)
            # Set adopting ases to adopting, returns index for list
#            self.tables.set_adopting_ases(self.percent, attacker)

            for adopt_policy in policies:
                attack = attack_generator.get_attack(attack_generator.test_index,
                                                     adopt_policy,
                                                     attacker,
                                                     victim,
                                                     attack_type)

                self.tests.append(Test(attack_type, attack, adopt_policy))
            attack_generator.test_index += 1

    def set_adopting_ases(self, policies):
        for i in range(0, len(self.tests), len(policies)):
            self.tables.set_adopting_ases(self.percent, self.tests[i].attack.attacker_asn)
