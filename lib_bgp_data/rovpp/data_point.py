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
import uuid

from .attack import Attack
from .enums import Attack_Types, Non_Default_Policies
from .tables import Attackers_Table, Victims_Table
from .tables import Simulation_Announcements_Table, Tracked_ASes_Table
from .test import Test

from ..base_classes import Parser
from ..database import Database
from ..utils import utils

class Data_Point(Parser):
    """Represents a data point on the graph"""

    def __init__(self, subtables, percent_iter, percent, csv_dir, deterministic):
        """stores relevant info"""

        # Subtables object
        self.tables = subtables
        # Percent iter is the index of the percent
        # This is legacy code that is no longer needed,
        # meant to have multiple levels adopting at different percents
        self.percent_iter = percent_iter
        # int
        self.percent = percent
        # path
        self.csv_dir = csv_dir
        self.deterministic = deterministic

    def get_data(self, exr_bash, exr_kwargs, pbars, atk_types, pols, trial, seeded_trial):
        """Runs test and stores data in the database"""

        # Get all possible tests and set them up
        for test in self.get_possible_tests(atk_types, pols, trial):
            # Yes, this isn't the fastest way to do it
            # But it's only for development, so whatever
            if pbars.current_trial != seeded_trial and seeded_trial is not None:
                pbars.update()
            else:
                # Run the test and insert into the database
                test.run(self.tables,
                         exr_bash,
                         exr_kwargs,
                         self.percent,
                         self.percent_iter,
                         pbars)

    def get_possible_tests(self, attack_types, policies, trial, set_up=True):
        """Gets all possible tests. Sets them up and returns them"""

        # For each type of hijack
        for attack_type in attack_types:
            # Sets adopting ases, returns hijack
            # We set up here so that we can compare one attack set up across
            # all the different policies
            attack = self.set_up_test(attack_type, trial) if set_up else None
            # For each type of policy, attempt to defend against that attack
            for adopt_policy in policies:
                yield Test(attack_type, attack, adopt_policy, self.tables)

    def set_up_test(self, attack_type, trial_num):
        """Sets up the tests by filling attackers and setting adopters"""

        random_seed = self.get_set_random_seed(attack_type, trial_num)
        # Fills the hijack table
        atk = self.fill_attacks(self.tables.possible_attackers, attack_type, trial_num)
        # Sets the adopting ases
        self.tables.set_adopting_ases(self.percent_iter, atk, random_seed)
        # Return the hijack class
        return atk

    def get_set_random_seed(self, attack_type, trial_num):
        if self.deterministic:
            seed = (str(attack_type)
                    + str(self.percent_iter)
                    + str(trial_num))
            random.seed(seed)
            return random.random()

    def fill_attacks(self, ases, attack_type, trial_num):
        """Sets up the attack, inserts into the db"""

        if self.deterministic:
            ases = sorted(ases)

        # Gets two random ases without duplicates
        attacker, victim = random.sample(ases, k=2)

        # Table schema: prefix | as_path | origin | time
        # NOTE: we use the time as an index for keeping track of atk/vic pairs

        # Subprefix hijack
        if attack_type == Attack_Types.SUBPREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/24', [attacker], attacker, 0]]
            victim_rows = [['1.2.0.0/16', [victim], victim, 0]]

        # Prefix hijack
        elif attack_type == Attack_Types.PREFIX_HIJACK:
            attacker_rows = [['1.2.0.0/16', [attacker], attacker, 0]]
            victim_rows = [['1.2.0.0/16', [victim], victim, 0]]

        # Unannounced prefix hijack
        elif attack_type == Attack_Types.UNANNOUNCED_PREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/24', [attacker], attacker, 0]]
            victim_rows = []

        elif attack_type == Attack_Types.UNANNOUNCED_SUPERPREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/24', [attacker], attacker, 0],
                              ['1.2.0.0/16', [attacker], attacker, 0]] 
            victim_rows = []

        elif attack_type == Attack_Types.SUPERPREFIX_HIJACK:
            attacker_rows = [['1.2.3.0/24', [attacker], attacker, 0],
                              ['1.2.0.0/16', [attacker], attacker, 0]]
            victim_rows = [['1.2.0.0/16', [victim], victim, 0]]

        elif attack_type == Attack_Types.LEAK:
            # CHange this to be the table later
            with Database() as db:
                sql = f"""SELECT * FROM leaks ORDER BY id LIMIT 1 OFFSET {trial_num}"""
                leak = db.execute(sql)[0]
                leaker_path = leak["example_as_path"]
                attacker = leak["leaker_as_number"]
                # Must cut off 1 after the attacker for proper seeding
                # Note that by one after the attacker, I mean from right to left
                # so if path was 51, 25, 63, ATTACKER, 81,
                # We want the new path to be 63, ATTACKER, 81
                # If there is prepending:
                # OG path:
                # 51, 25, 63, ATTACKER, ATTACKER, ATTACKER, 81,
                # New path:
                # 63, ATTACKER, ATTACKER, ATTACKER, 81,
                new_leaker_path = []
                about_to_break = False
                for asn in reversed(leaker_path):
                    new_leaker_path.append(asn)
                    # Must have second equality here just in case attacker prepends
                    # (prepending is when an asn is listed multiple times
                    #  we want one after the attacker, but if the attacker is repeated
                    #  we must keep going)
                    if about_to_break and asn != attacker:
                        break
                    if asn == attacker:
                        about_to_break = True
                new_leaker_path.reverse()        
                attacker_rows = [[leak["leaked_prefix"],
                                  new_leaker_path,
                                  leak["example_as_path"][-1],
                                  0]]
                victim_rows = []

        # Format the lists to be arrays for insertion into postgres
        for rows in [attacker_rows, victim_rows]:
            for row in rows:
                if len(row) > 0:
                    row[1] = str(row[1]).replace("[", "{").replace("]", "}")

        csv_path = join(self.csv_dir, "{}.csv")

        # For each type of attacker victim definition
        for atk_def, rows, Table in zip(["attackers", "victims"],
                                        [attacker_rows, victim_rows],
                                        [Attackers_Table, Victims_Table]):
            # Insert into the database
            utils.rows_to_db(rows, csv_path.format(atk_def), Table)

        # Change to use simulation_announcements
        utils.rows_to_db(attacker_rows + victim_rows,
                         csv_path.format("agg_ann"),
                         Simulation_Announcements_Table)
        attacker_victim_rows = [[attacker, True, False]]
        if len(victim_rows) > 0:
            attacker_victim_rows.append([victim, False, True])
        utils.rows_to_db(attacker_victim_rows,
                         csv_path.format("atk_vic_info"),
                         Tracked_ASes_Table)

        return Attack(attacker_rows, victim_rows)
