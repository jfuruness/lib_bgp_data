#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains ROVPP_Simulator which runs attack/defend simulations

See README for in depth explanation
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from multiprocessing import cpu_count
import os
from random import random
import logging

import numpy as np
from tqdm import trange

from .attack import Attack_Generator
from .data_point import Data_Point
from .enums import Attack_Types, Non_Default_Policies
from .multiline_tqdm import Multiline_TQDM
from .subtables_base import Subtables
from .tables import Simulation_Results_Table, Attackers_Table, Victims_Table
from .tables import Tests_Table


from ..base_classes import Parser
from ..relationships_parser import Relationships_Parser
from ..utils import utils
# Done this way to fix circular imports
from .. import extrapolator_parser as exr


class ROVPP_Simulator(Parser):
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    def _run(self,
             percents=[1,2,3,4,5,10,20,40,60,80,99],
             num_trials=2,
             exr_bash=None,
             attack_types=Attack_Types.__members__.values(),
             policies=Non_Default_Policies.__members__.values()):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        assert num_trials <= 15000, "Change prefix generator func to have more prefixes"

        # Gets relationships table
        Relationships_Parser(**self.kwargs).parse_files()

        tables = Subtables(percents)
        tables.fill_tables()

        data_pts = [Data_Point(tables, i, p) for i, p in enumerate(percents)]

        # The reason we run tqdm off the number of trials
        # And not number of data points is so that someone can input the
        # deterministic trial number and have it jump straight to that trial
        # In addition - the reason we have multiple bars is so that we can
        # display useful stats using the bar

        attack_generator = Attack_Generator()
        # Generate all the tests to run at once
        for trial in trange(num_trials, desc="Generating input"):
            for data_pt in data_pts:
                data_pt.get_possible_tests(attack_types, policies, attack_generator)
                # Note that the thing that takes a while is list rewrites
                # We could initialize the list to a certain size to start
                # But for now that's over optimizing
                # Since this part takes < 5 min and exr takes a day
                # And in addition we could multiprocess it with multi db or whatnot
        attack_rows = []
        victim_rows = []
        for data_pt in data_pts:
            for test in data_pt.tests:
                attack_rows.append(test.attack.attacker_row)
                if test.attack.victim_row is not None:
                    victim_rows.append(test.attack.victim_row)

        for rows, atk_vic_Table in zip([attack_rows, victim_rows],
                                       [Attackers_Table, Victims_Table]):
            csv_path = os.path.join(self.csv_dir, atk_vic_Table.name)
            utils.rows_to_db(rows, csv_path, atk_vic_Table)
        with Database() as db:
            db.execute("DROP TABLE IF EXISTS attacker_victims")
            sql = """CREATE UNLOGGED TABLE IF NOT EXISTS attacker_victims AS(
    SELECT a.prefix AS attacker_prefix, a.as_path AS attacker_as_path, a.origin AS attacker_origin,
        v.prefix AS victim_prefix, v.as_path AS victim_as_path, v.origin as victim_origin,
        a.list_index, a.policy_val, a.percent_iter, a.attack_type
    FROM attackers a
    LEFT JOIN victims v ON v.list_index = a.list_index AND v.policy_val = a.policy_val
);"""
            db.execute(sql)
        ases_dict = {x.Input_Table.name: x.ases for x in tables.tables}
        table_classes = {x.Input_Table.name: x.Input_Table.__class__ for x in tables.tables}
        iterable = [(ases_dict,
                    [dp.tests[i].attack.attacker_asn for i in range(0, len(dp.tests), len(policies))],
                    dp.percent,
                    table_classes) for dp in data_pts]
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            mp_dps = list(executor.map(self.set_adopting_ases, iterable))
        drop_sqls = []
        for table in tables.tables:
            drop_sqls.append(f"DROP TABLE IF EXISTS {table.Input_Table.name}")
        create_sqls = []
        for subtable_name, subtable_class in table_classes.items():
            names = [mp_dp[subtable_name] for mp_dp in mp_dps]
            as_types_str = " || ".join(f"{name}.as_types" for name in names)
            inner_join_str = "".join([f"INNER JOIN {name} ON {name}.asn = {names[0]}.asn " for name in names[1:]])
            sql = f"""CREATE UNLOGGED TABLE {subtable_name} AS (
                  SELECT {names[0]}.asn, {as_types_str} AS as_types FROM {names[0]} {inner_join_str});"""
            create_sqls.append(sql)
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            list(executor.map(exec_sql, zip(drop_sqls, create_sqls)))
            
#       i tables.write_to_postgres(mp_dps, self.csv_dir)
        logging.info("Running exr")
        # Run extrapolator - feed as input the policy nums to run
        exr.ROVPP_Extrapolator_Parser(**self.kwargs).run(table_names=[k for k,v in table_classes.items()])
        # inputs normally exr_bash, exr_kwargs, self.percent, pbars
        # Make ribs out table properly
        return
#        input("!")

        # Clear the table that stores all trial info
        with Simulation_Results_Table(clear=True) as _:
            pass
        # Probably should do this using multiprocessing
        with Multiline_TQDM(len(trials)) as pbars:
            for test in tests:
                test.analyze_output(tables)
                data_pt.get_data(exr_bash,
                                 self.kwargs,
                                 pbars,
                                 attack_types,
                                 adopt_policy_types,
                                 seeded)
                pbars.update()

        tables.close()

    def set_adopting_ases(self, iterable):#subtable_ases_dict, tests, percent):
        subtable_ases_dict, attackers, percent, table_classes = iterable


        """
preinitializing a list of zeros for 1k: 5 min 31 seconds
starting without a list of zeros for 1k: 5 min and 5 seconds
doing it with random.random instead of numpy: 2 min 39s
doing it with massive dict comp: 2:57,
doing it without massive dict comp: 2:56 same time whatevs
doing it with massive dict comp:
        """

        for t_name, table_class in table_classes.items():
            table_class.name = f"{t_name}_{percent}"

        # Note: tried doing different logic for possible attackers tables, made it longer
        for t_name, ases_dict in subtable_ases_dict.items():
            rows = []
            new_percents_attackers = []
            for attacker in attackers:
                maybe_adopters = len(ases_dict) - (1 if attacker in ases_dict else 0)
                num_adopters = maybe_adopters * percent // 100
                new_percents_attackers.append((num_adopters / maybe_adopters, attacker))
            for _as in ases_dict:
                rows.append([_as, "{" + str(list(random() < new_percent and _as != attacker for (new_percent, attacker) in new_percents_attackers))[1:-1] + "}"])
            csv_path = os.path.join(self.csv_dir, f"{table_classes[t_name].name}.csv")
            utils.rows_to_db(rows, csv_path, table_classes[t_name])
        return {k: v.name for k, v in table_classes.items()}
"""
                ases_dict[_as] = [False] * len(attackers)
            for i, attacker in enumerate(attackers):
                maybe_adopters = len(ases_dict) - (1 if attacker in ases_dict else 0)
                num_adopters = maybe_adopters * percent // 100
                new_percent = num_adopters / maybe_adopters
                for j, (_as, as_types) in enumerate(ases_dict.items()):
                    if rands[i + j] < new_percent and _as != attacker:
                        as_types[i] = True
        return subtable_ases_dict"""

from ..database import Database
def exec_sql(sqls):
    with Database() as db:
        for sql in sqls:
            db.execute(sql)
