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

from ...simulator import Simulator
from ...subtables_base import Subtables
from ...subtables.tables import ASes_Subtable, Subtable_Forwarding_Table

from .....extrapolator import Simulation_Extrapolator_Wrapper as Sim_Exr
from .....collectors.relationships.tables import Peers_Table, Provider_Customers_Table

class Graph_Tester:
    def _run_simulator(self,
                       percents=[1],
                       num_trials=2,
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
                       attacker: int =None,
                       victim: int =None):

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
            exr_cls(**self.sim.kwargs).install(force=True)
            path = os.path.join(self.sim.csv_dir, "rels.csv")
            utils.rows_to_db(peer_rows, path, Peers_Table)
            utils.rows_to_db(provider_customer_rows, path, Provider_Customers_Table)

        # TODO: patch subtables get_tables
        #       should be subtables object with just one table
        def subtables_get_tables_patch(subtable_self, percents, *args, **kwargs):
            class Sim_Test_ASes_Table(ASes_Subtable):
                input_name = name = "sim_test_ases"
                adopting_rows = adopting_rows
                def set_adopting_ases(self, *args, **kwargs):
                    self.fill_table()
                @property
                def Forwarding_Table(self):
                    return Sim_Test_ASes_Forwarding_Table
                def fill_table(self, *args):
                    path = f"/tmp/{datetime.now()}{str(args)}.csv"
                    utils.csv_to_db(self.adopting_rows, path, self.__class__)

            class Sim_Test_ASes_Forwarding_Table(Sim_Test_ASes_Table,
                                                 Subtable_Forwarding_Table):
                name = "sim_test_ases_forwarding"


            subtable_self.tables = [Subtable(Sim_Test_ASes_Table,
                                             percents,
                                             possible_attacker=True)]
        # TODO: patch ASes subtables set_adopting_ases
        #       should update the table to be what you pass in
        #       NOTE: did this in the overriden subtable

        # TODO: patch random.sample to select both vic and atk correctly
        def random_sample_patch(*args):
            return attacker, victim

        with patch.object(Simulator,
                          "_redownload_base_data",
                          _redownload_base_data_patch):
            with patch.object(Subtables,
                              "get_tables",
                              subtables_get_tables_patch):
                with patch("random.sample", random_sample_patch):
                    Simulator(percents,
                              num_trials,
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


    def validate_input(self, *args):
        for arg in args:
            assert len(arg) == 1, "Each arg must be of length one if a list"
