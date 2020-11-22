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
from .test import Test

from ..base_classes import Parser
from ..database import Database
from ..mrt_parser.tables import MRT_W_Metadata_Table
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

        # Table schema: prefix | as_path | origin | time | monitor_asn |
        # prefix_id | origin_id | prefix_origin_id | block_id |
        # roa_validity | block_prefix_id

        # ROA validity: 0 valid, 1 unknown, 2 invalid by origin, 3 invalid by len
        # 4 invalid by origin and len
        # Subprefix hijack
        if attack_type == Attack_Types.SUBPREFIX_HIJACK:
            attacker_rows = [{"prefix": '1.2.3.0/24',
                              "as_path": [attacker],
                              "origin": attacker,
                              "prefix_id": 0,
                              "origin_id": 0,
                              "prefix_origin_id": 0,
                              "roa_validity": 4}]
            victim_rows = [{"prefix": '1.2.3.0/24',
                            "as_path": [victim],
                            "origin": victim,
                            "prefix_id": 1,
                            "origin_id": 1,
                            "prefix_origin_id": 1,
                            "roa_validity": 0}]

        # Prefix hijack
        elif attack_type == Attack_Types.PREFIX_HIJACK:
            attacker_rows = [{"prefix": '1.2.0.0/16',
                              "as_path": [attacker],
                              "origin": attacker,
                              "prefix_id": 0,
                              "origin_id": 0,
                              "prefix_origin_id": 0,
                              "roa_validity": 2}]
            victim_rows = [{"prefix": '1.2.0.0/16',
                            "as_path": [victim],
                            "origin": victim,
                            "prefix_id": 0,
                            "origin_id": 1,
                            "prefix_origin_id": 1,
                            "roa_validity": 0}]
        # Unannounced prefix hijack
        elif attack_type == Attack_Types.UNANNOUNCED_PREFIX_HIJACK:
            attacker_rows = [{"prefix": '1.2.3.0/24',
                              "as_path": [attacker],
                              "origin": attacker,
                              "prefix_id": 0,
                              "origin_id": 0,
                              "prefix_origin_id": 0,
                              "roa_validity": 4}]
            victim_rows = []

        elif attack_type == Attack_Types.UNANNOUNCED_SUPERPREFIX_HIJACK:
            # ROA for subprefix not superprefix
            attacker_rows = [{"prefix": '1.2.0.0/16',
                              "as_path": [attacker],
                              "origin": attacker,
                              "prefix_id": 0,
                              "origin_id": 0,
                              "prefix_origin_id": 0,
                              # ROA for superprefix is 1 for unknown
                              "roa_validity": 1},
                              {"prefix": '1.2.3.0/24',
                               "as_path": [attacker],
                               "origin": attacker,
                               "prefix_id": 1,
                               "origin_id": 0,
                               "prefix_origin_id": 1,
                               "roa_validity": 4}]
            victim_rows = []

        elif attack_type == Attack_Types.SUPERPREFIX_HIJACK:
            # ROA for subprefix not superprefix
            attacker_rows = [{"prefix": '1.2.0.0/16',
                              "as_path": [attacker],
                              "origin": attacker,
                              "prefix_id": 0,
                              "origin_id": 0,
                              "prefix_origin_id": 0,
                              # ROA for superprefix is 1 for unknown
                              "roa_validity": 1},
                              {"prefix": '1.2.3.0/24',
                               "as_path": [attacker],
                               "origin": attacker,
                               "prefix_id": 1,
                               "origin_id": 0,
                               "prefix_origin_id": 1,
                               "roa_validity": 4}]
            victim_rows = [{"prefix": '1.2.0.0/16',
                            "as_path": [victim],
                            "origin": victim,
                            "prefix_id": 1,
                            "origin_id": 1,
                            "prefix_origin_id": 2,
                            "roa_validity": 0}]

        elif attack_type == Attack_Types.LEAK:
            assert False, "Not yet implimented"
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
                                  1]]
                victim_rows = []

        rows = []
        # Format the lists to be arrays for insertion into postgres
        for list_of_rows, time_val in zip([attacker_rows, victim_rows], [1, 0]):
            for mrt_dict in list_of_rows:
                mrt_dict["time"] = time_val
                mrt_dict["block_id"] = 0
                mrt_dict["monitor_asn"] = 0
                mrt_dict["block_prefix_id"] = mrt_dict["prefix_id"]
                row = []
                for col in MRT_W_Metadata_Table.columns:
                    cur_item = mrt_dict.get(col)
                    assert cur_item is not None or col in ["monitor_asn", "block_id"], col
                    if isinstance(cur_item, list):
                        cur_item = str(cur_item).replace("[", "{").replace("]", "}")
                    row.append(cur_item)
                rows.append(row)

        path = join(self.csv_dir, "mrts.csv")
        utils.rows_to_db(rows, path, MRT_W_Metadata_Table)

        return Attack(attacker_rows, victim_rows)
