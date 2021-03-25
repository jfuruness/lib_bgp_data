#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
import copy
from ..tables import Top_100_ASes_Table
from ..... import Relationships_Parser, AS_Rank_Website_Parser, MRT_Parser, MRT_Metadata_Parser
from ..subtables_base import Subtable
from ..output_subtables import Output_Subtables, Output_Subtable
from .....extrapolator import Simulation_Extrapolator_Wrapper, Simulation_Extrapolator_Forwarding_Table
from ...attacks import Subprefix_Hijack
from ....enums import AS_Types
from .....collectors import Relationships_Parser, AS_Rank_Website_Parser
from ... import Simulator

class Test_Output_Subtable:

    table = Top_100_ASes_Table
    percents = 5
    ases = {13335: {'received_from_asn': 5000, 'impliment': 1},
           5000: {'received_from_asn': 64514, 'impliment': 0},
           64514: {'received_from_asn': 64514, 'impliment':0}}
    attack = Subprefix_Hijack(5000, 3000)

    # tables = [Top_100_ASes_table, Edges, etc]

    # likely move to conftest.py
    @pytest.fixture(scope="class")
    def subtable(self):
        #Relationships_Parser().run()
        #AS_Rank_Website_Parser().run() 

        Simulator().run(redownload_base_data=True)
        #subtable.connect()
        return Subtable(self.table, self.percents)

    def test_store(self):
        """Check insertion"""
        # does this just store one?

    #@pytest.mark.curr
    def test_get_traceback_data(self, subtable):
        """actually no clue yet

        #Simulation_Extrapolator_Wrapper().run(table_names=[self.table], rounds=1)
        #with self.table() as _db:
            #_db.fill_table()
        #    all_ases = {x["asn"]: x for x in _db.get_all()}


        forwarding_table = self.table().Forwarding_Table()
        forwarding_table.fill_forwarding_table(1)
        all_ases = {x["asn"]: x for x in forwarding_table.get_all()}

        import copy
        subtable_ases = copy.deepcopy(all_ases)

        #subtable_ases = {x["asn"]: x for x in subtable.table.Forwarding_Table().get_all()}
        # We don't want to track the attacker, faster than filtering dict comp
        attack = Subprefix_Hijack(55, 66)
        for uncountable_asn in [attack.attacker, attack.victim]:
            if uncountable_asn in subtable_ases:
                del subtable_ases[uncountable_asn]
        """
        # lol?
        subtable_ases = {13335: {'received_from_asn': 5000, 'impliment': 1},
                        5000: {'received_from_asn': 64514, 'impliment': 0},
                        64514: {'received_from_asn': 64514, 'impliment':0}}

        attack = Subprefix_Hijack(5000, 3000)

        assert subtable._get_traceback_data(subtable_ases, subtable_ases, attack)[64514] == {0: 2, 1: 1}

        #{64512: {0: 0, 1: 0}, 64513: {0: 0, 1: 0}, 64514: {0: 2, 1: 1}}

    @pytest.mark.skip()
    def test_get_visible_hijack_data(self):
        """return dict of adopting and non-adopting count"""

        t = Output_Subtable()
        attack = Subprefix_Hijack(5000, 3000)
        ret = t._get_visible_hijack_data(None, attack, 1)
        #assert ret[AS_Types.COLLATERAL] == #?
        #assert ret[AS_Types.ADOPTING] == #?

    def test_print_loop_debug_data(self, subtable):
        """Exit with code 1 when there's a loop"""

        og_asn = 13335
        og_as_data = {'received_from_asn': 5000, 'impliment': 1}

        with pytest.raises(SystemExit) as exit:
            # whereas other functions know the end condition
            # it will just be treated as a loop here
            # which is fine for testing purposes
            # since this function will only be called when there's a loop
            subtable._print_loop_debug_data(self.ases,
                                            og_asn,
                                            og_as_data,
                                            self.attack)
        assert exit.value.code == 1

    @pytest.mark.curr
    def test_get_control_plane_data(self, subtable):
        """i guess these are also counts"""

        Relationships_Parser().run() # fill the necessary ases table
        AS_Rank_Website_Parser().run()
        MRT_Parser().run()
        MRT_Metadata_Parser().run() # can this just run mrt_parser if mrt_announcements table not filled..
        # think the table parameter is rovpp policy table according to doc. idk what that EXACTLY mean
        Simulation_Extrapolator_Wrapper()._run([self.table.name], 1, None, None, None, None, None)
        #Simulation_Extrapolator_Forwarding_Table().fill_table()
        subtable.connect() # need to set forwarding table?
        subtable.Forwarding_Table.fill_forwarding_table(1)
        #subtable.close()
        subtable.Input_Table.fill_table(self.table.name)
        ret = subtable._get_control_plane_data(self.attack)
        print(ret)
