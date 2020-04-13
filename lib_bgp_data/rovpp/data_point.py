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

from .attack import Attack
from .enums import Attack_Types, Non_Default_Policies
from .test import Test

from ..base_classes import Parser


class Data_Point(Parser):
    def __init__(self, subtables, percent_iter, percent, csv_dir):
        self.tables = subtables
        self.percent_iter = percent_iter
        self.percent = percent
        self.csv_dir = csv_dir

    def get_data(self, exr_bash, exr_kwargs, pbars, atk_types, pols):
        for test in self.get_possible_tests(atk_types, pols):
            test.run(self.tables, exr_bash, exr_kwargs, self.percent, pbars)

    def get_possible_tests(self, attack_types, policies, set_up=True):
        for attack_type in attack_types:
            # Sets adopting ases, returns hijack
            attack = self.set_up_test(attack_type) if set_up else None

            for adopt_policy in policies:
                yield Test(attack_type, attack, adopt_policy)

    def set_up_test(self, attack_type):
        # Fills the hijack table
        self.populate_scenarios(self.tables.possible_attackers, attack_type)
        # Sets the adopting ases
        self.tables.set_adopting_ases(self.percent_iter, hijack.attacker_asn)
        # Return the hijack class
        return attack

    def populate_scenarios(self, ases, attack_type):
        # Gets two random ases without duplicates
        attacker, victim = sample(ases, k=2)

        # Table schema: prefix | as_path | origin | time
        # NOTE: we use the time as an index for keeping track of atk/vic pairs

        if attack_type == Attack_Types.SUBPREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/24', [attacker], attacker, 0]]
            victim_rows = [['1.2.3.0/16', [victim], victim, 0]]

        elif attack_type == Attack_Types.PREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/16', [attacker], attacker, 0]]
            victim_rows = [['1.2.3.0/16', [victim], victim, 0]]

        elif attack_type == Attack_Types.UNANNOUNCED_PREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/24', [attacker], attacker, 0]]
            victim_rows = []

        for atk_def, rows, Table in zip(["attackers", "victims"],
                                        [attacker_rows, victim_rows],
                                        [Attackers_Table, Victims_Table]):
            csv_path = os.path.join(csv_dir, f"{atk_def}.csv")
            utils.rows_to_db(rows, csv_path, Table)

        return Attack(attacker_rows, victim_rows)
