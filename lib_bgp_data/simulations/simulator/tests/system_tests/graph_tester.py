#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from copy import deepcopy
import os
from unittest.mock import patch
from datetime import datetime

from ....enums import Data_Plane_Conditions
from ...simulator import Simulator
from ...tables import Simulation_Results_Table
from ...subtables.output_subtables import Output_Subtable, Output_Subtables
from ...subtables.subtables_base import Subtables, Subtable

from ...subtables.tables import ASes_Subtable, Subtable_Forwarding_Table

from .....extrapolator import Simulation_Extrapolator_Wrapper as Sim_Exr
from .....collectors.relationships.tables import Peers_Table, Provider_Customers_Table
from .....utils import utils

class Graph_Tester:
    def _test_graph(self,
                    percents=[1],
                    num_trials=1,
                    exr_cls=Sim_Exr,  # For development only
                    attack_types=[],
                    adopt_policies=[],
                    rounds=1,
                    extra_bash_args_1=[None],
                    extra_bash_args_2=[None],
                    extra_bash_args_3=[None],
                    extra_bash_args_4=[None],
                    extra_bash_args_5=[None],
                    ### Test specific args ###
                    # Format of peer_asn_1, peer_asn_2
                    peer_rows=[],
                    # Format of provider, customer
                    provider_customer_rows=[],
                    # Format of asn, default, adopt_bool
                    adopting_rows=[],
                    attacker: int = None,
                    victim: int = None,
                    exr_output=[],
                    results_dict={},
                    traceback_dict={}):

        self.sim = Simulator()

        self.validate_input(percents,
                            attack_types,
                            adopt_policies,
                            extra_bash_args_1,
                            extra_bash_args_2,
                            extra_bash_args_3,
                            extra_bash_args_4,
                            extra_bash_args_5)
        # TODO: patch redownload base data
        #       pass in relationships table, redownload exr
        def _redownload_base_data_patch(*args, **kwargs):
            # forces new install of extrapolator
            print("Later should install exr every time!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            #exr_cls(**self.sim.kwargs).install(force=True)
            path = os.path.join(self.sim.csv_dir, "rels.csv")
            utils.rows_to_db(peer_rows, path, Peers_Table)
            utils.rows_to_db(provider_customer_rows, path, Provider_Customers_Table)

        # TODO: patch subtables get_tables
        #       should be subtables object with just one table
        def subtables_get_tables_patch(subtable_self, percents, *args, **kwargs):
            adptng_rows = adopting_rows # needs to be available in this scope
            class Sim_Test_ASes_Table(ASes_Subtable):
                input_name = name = "sim_test_ases"
                columns = ["asn", "as_type", "impliment"]
                def _create_tables(self):
                    sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                            asn bigint,
                            as_type integer,
                            impliment boolean);
                            """
                    self.cursor.execute(sql)
                def set_adopting_ases(self, *args, **kwargs):
                    self.fill_table()
                @property
                def Forwarding_Table(self):
                    return Sim_Test_ASes_Forwarding_Table
                def fill_table(self, *args):
                    path = f"/tmp/{datetime.now()}_system_tests.csv"
                    utils.rows_to_db(adptng_rows, path, self.__class__)
                def change_routing_policies(self, *args):
                    # We never need to call this func for these tests
                    # This will allow us to mix multiple policies
                    pass

            class Sim_Test_ASes_Forwarding_Table(Sim_Test_ASes_Table,
                                                 Subtable_Forwarding_Table):
                name = "sim_test_ases_forwarding"


            subtable_self.tables = [Subtable(Sim_Test_ASes_Table,
                                             percents, #)] #edge_atk, etc_atk, top_atk,
                                             possible_attacker=True)]
        # TODO: patch ASes subtables set_adopting_ases
        #       should update the table to be what you pass in
        #       NOTE: did this in the overriden subtable

        # TODO: patch random.sample to select both vic and atk correctly
        def random_sample_patch(*args, **kwargs):
            return victim, attacker

        # Checks the output
        def _run_test(self, exr_table):
            if not exr_output:
                return
            table_rows = exr_table.get_all()
            
            # Format rows to get rid of defaultdict
            formatted_table_rows = []
            for table_row in table_rows:
                formatted_table_rows.append(
                    {"asn": table_row.get("asn"),
                     "prefix": table_row.get("prefix"),
                     "origin": table_row.get("origin"),
                     "received_from_asn": table_row.get("received_from_asn")})


            # Make sure all test data is in raw data
            for test_row in exr_output:
                try:
                    assert test_row in formatted_table_rows
                except AssertionError as e:
                    from pprint import pprint
                    print("\n" * 10)
                    print("Expected row that is not in raw" + str(test_row))
                    print("raw rows")
                    pprint(formatted_table_rows)
                    print("same asn")
                    for row in formatted_table_rows:
                        if test_row["asn"] == row["asn"]:
                            print(row)
                    print("\n" * 10)
                    raise e
                        
            # Make sure all raw data is in test data
            for raw_row in formatted_table_rows:
                try:
                    assert raw_row in exr_output
                except AssertionError as e:
                    from pprint import pprint
                    print("\n" * 10)
                    print("raw row that is not in expected rows" + str(raw_row))
                    print("expected rows")
                    pprint(exr_output)
                    print("\n" * 10)
                    raise e

        og_traceback = deepcopy(Output_Subtable._get_traceback_data)
        def _get_traceback_data_patch(self, *args, **kwargs):


            conditions = {x.value: x for x in list(Data_Plane_Conditions)}
            # This is for the professor convenience
            ases = {x["asn"]: x for x in self.Forwarding_Table.get_all()}
            traceback_results = {}
            for og_asn, og_as_data in ases.items():
                asn, as_data = og_asn, og_as_data
                looping = True
                # Path should never be longer than 64
                for _ in range(64):
                    # Conds are end conditions. See README.
                    if as_data["received_from_asn"] in conditions:
                        traceback_results[og_asn] = conditions[as_data["received_from_asn"]]
                        looping = False
                        break
                    else:
                        asn = as_data["received_from_asn"]
                        as_data = ases[asn]
                assert not looping, "Traceback is looping"
            for asn, condition in traceback_dict.items():
                if asn not in traceback_results:
                    raise Exception(f"{asn} not tracked in traceback? Was it an attacker/victim?")
                err = f"{asn} was {traceback_results[asn].name}, not {condition.name}"
                assert traceback_results[asn] == condition, err
            return og_traceback(self, *args, **kwargs)

        with patch.object(Simulator,
                          "_redownload_base_data",
                          _redownload_base_data_patch):
            with patch.object(Subtables,
                              "get_tables",
                              subtables_get_tables_patch):
                with patch("random.sample", random_sample_patch):
                    with patch.object(Sim_Exr, "_run_test", _run_test):
                        with patch.object(Output_Subtable,
                                          "_get_traceback_data",
                                          _get_traceback_data_patch):
                            print('Running test simulation')
                            Simulator().run(percents,
                                      num_trials=num_trials,
                                      exr_cls=exr_cls,
                                      attack_types=attack_types,
                                      adopt_policies=adopt_policies,
                                      rounds=rounds,
                                      extra_bash_args_1=extra_bash_args_1,
                                      extra_bash_args_2=extra_bash_args_2,
                                      extra_bash_args_3=extra_bash_args_3,
                                      extra_bash_args_4=extra_bash_args_4,
                                      extra_bash_args_5=extra_bash_args_5,
                                      redownload_base_data=True)
        with Simulation_Results_Table() as db:
            assert num_trials == 1, "Must be one for this. Can extend later"
            result = db.get_all()[0]
            for k, v in results_dict.items():
                assert result[k] == v


    def validate_input(self, *args):
        for arg in args:
            assert len(arg) == 1, "Each arg must be of length one if a list"
