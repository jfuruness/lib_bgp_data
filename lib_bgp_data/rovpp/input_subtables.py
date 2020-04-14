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


class Input_Subtables:
    """Contains subtable functionality for pre exr functions"""

    def fill_input_tables(self):
        for subtable in self.input_tables:
            subtable.clear_table()
            subtable.fill_input_table(self.tables)

    def set_adopting_ases(self, percent_iter, attack, seeded):
        for subtable in self.tables:
            subtable.set_adopting_ases(percent_iter, attack, seeded)

    def change_routing_policies(self, policy):
        """Changes the routing policy for that percentage of ASes"""

        logging.debug("About to change the routing policies")
        for sub_table in self.tables:
            sub_table.change_routing_policies(policy)

    @property
    def possible_attackers(self):
        possible_attacker_ases = []
        # For all tables where possible attacker is true
        for _table in self.tables:
            possible_attacker_ases.extend(_table.get_possible_attackers())
        return possible_attacker_ases


class Input_Subtable:
    """Subtable class for ease of use"""

    def set_adopting_ases(self, iteration_num, attack, deterministic):
        self.Input_Table.set_adopting_ases(self.percents[iteration_num],
                                           attack.attacker_asn,
                                           deterministic)

    def change_routing_policies(self, policy):
        if self.permanent_policy is not None:
            policy = self.permanent_policy
        self.Input_Table.change_routing_policies(policy)

    def get_possible_attackers(self):
        possible_attackers = []
        if self.possible_attacker:
            possible_attackers = [x["asn"] for x in self.Input_Table.get_all()]
        return possible_attackers
