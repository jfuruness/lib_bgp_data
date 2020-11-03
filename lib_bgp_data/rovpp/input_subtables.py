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
        """Fills all the subtables"""

        for subtable in self.input_tables:
            subtable.clear_table()
            subtable.fill_input_table(self.tables)

    def set_adopting_ases(self, percent_iter, attack, random_seed):
        """Sets adopting ases"""

        for subtable in self.tables:
            subtable.set_adopting_ases(percent_iter, attack, self.names, random_seed)

    def change_routing_policies(self, policy):
        """Changes the routing policy for that percentage of ASes"""

        logging.debug("About to change the routing policies")
        for sub_table in self.tables:
            sub_table.change_routing_policies(policy)

    @property
    def possible_attackers(self):
        """Returns all possible attackers

        Note that some subtables will yeild no attackers, which is why
        this function is neccessary. For example, no top level ASes are
        allowed to become hijackers"""

        possible_attacker_ases = []
        # For all tables where possible attacker is true
        for _table in self.tables:
            possible_attacker_ases.extend(_table.get_possible_attackers())
        return possible_attacker_ases


class Input_Subtable:
    """Subtable class for ease of use"""

    def set_adopting_ases(self, iteration_num, attack, names, random_seed):
        """Sets adopting ases"""

        # Cleared instead of updated due to speed, much faster
        self.Input_Table.clear_table()
        self.Input_Table.fill_table(names)
        self.Input_Table.set_adopting_ases(self.percents[iteration_num],
                                           attack.attacker_asn, random_seed)

    def change_routing_policies(self, policy):
        """Changes routing policies of the subtable"""

        if self.permanent_policy is not None:
            policy = self.permanent_policy
        self.Input_Table.change_routing_policies(policy)

    def get_possible_attackers(self):
        """Returns possible attackers for this subtable"""

        possible_attackers = []
        if self.possible_attacker:
            possible_attackers = [x["asn"] for x in self.Input_Table.get_all()]
        return possible_attackers
