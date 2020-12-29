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
import random

from .test import Test

from ....collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table
from ....utils import utils
from ....utils.base_classes import Parser


class Data_Point(Parser):
    """Represents a data point on the graph"""

    def __init__(self, tables, percent_iter, percent, csv_dir, deterministic):
        """stores relevant info"""

        # Subtables object
        self.tables = tables
        # Percent iter is the index of the percent
        # This is legacy code that is no longer needed,
        # meant to have multiple levels adopting at different percents
        self.percent_iter = percent_iter
        self.p_iter = percent_iter
        # int
        self.percent = percent
        # path
        self.csv_dir = csv_dir
        # Helpful for debugging
        self.deterministic = deterministic

    def get_data(self,
                 pbars,
                 atk_classes,
                 pols,
                 trial,
                 seeded_trial=None,
                 exr_bash=None,
                 exr_kwargs=None):
        """Runs test and stores data in the database"""

        # Get all possible tests and set them up
        for test in self.get_possible_tests(atk_classes, pols, trial):
            # Yes, this isn't the fastest way to do it
            # But it's only for development, so whatever
            # Skips trials if we have seeded the trial
            if (pbars.current_trial != seeded_trial
                    and seeded_trial is not None):

                pbars.update()
            else:
                # Run the test and insert into the database
                test.run(pbars, exr_bash=exr_bash, exr_kwargs=exr_kwargs)

    def get_possible_tests(self, attack_classes, policies, trial, set_up=True):
        """Gets all possible tests. Sets them up and returns them"""

        # For each type of hijack
        for attack_cls in attack_classes:
            # Sets adopting ases, returns hijack
            # We set up here so that we can compare one attack set up across
            # all the different policies
            atk = self.set_up_test(attack_cls, trial) if set_up else None
            # For each type of policy, attempt to defend against that attack
            for pol in policies:
                yield Test(atk, pol, self.tables, self.percent, self.p_iter)

    def set_up_test(self, attack_cls, trial_num):
        """Sets up the tests by filling attackers and setting adopters"""

        random_seed = self.get_set_random_seed(attack_cls, trial_num)
        # Fills the hijack table
        atk = self.fill_attacks(self.tables.possible_attackers,
                                attack_cls,
                                trial_num)
        # Sets the adopting ases
        self.tables.set_adopting_ases(self.percent_iter, atk, random_seed)
        # Return the hijack class
        return atk

    def get_set_random_seed(self, attack_cls, trial_num):
        if self.deterministic:
            random.seed(f"{attack_cls}{self.percent_iter}{trial_num}")
            return random.random()

    def fill_attacks(self, ases, Attack_Cls, trial_num):
        """Sets up the attack, inserts into the db"""

        if self.deterministic:
            ases = sorted(ases)

        # Gets two random ases without duplicates
        victim, attacker = random.sample(ases, k=2)

        attack = Attack_Cls(victim, attacker)

        path = join(self.csv_dir, "mrts.csv")
        utils.rows_to_db(attack.db_rows, path, MRT_W_Metadata_Table)

        return attack
