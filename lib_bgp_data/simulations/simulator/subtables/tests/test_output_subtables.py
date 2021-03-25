#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from ..tables import Top_100_ASes_Table
from ..subtables_base import Subtable
from ..output_subtables import Output_Subtables, Output_Subtable
from .....extrapolator import Simulation_Extrapolator_Forwarding_Table
from ...attacks import Subprefix_Hijack
from ....enums import AS_Types
from .....collectors import Relationships_Parser, AS_Rank_Website_Parser
from ... import Simulator

class Test_Output_Subtable:

    table = Top_100_ASes_Table
    percents = 5

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

    @pytest.mark.curr
    def test_get_traceback_data(self, subtable):
        """actually no clue yet"""
        with Simulation_Extrapolator_Forwarding_Table(round_num=0) as _db:
            #_db.fill_table()
            all_ases = {x["asn"]: x for x in _db.get_all()}

        subtable_ases = {x["asn"]: x for x in subtable.table.Forwarding_Table.get_all()}
        # We don't want to track the attacker, faster than filtering dict comp
        for uncountable_asn in [attack.attacker, attack.victim]:
            if uncountable_asn in subtable_ases:
                del subtable_ases[uncountable_asn]

        attack = Subprefix_Hijack(55, 66)
        print(subtable._get_traceback_data(subtable_ases, all_ases, attack))

    def test_get_visible_hijack_data(self):
        """return dict of adopting and non-adopting count"""

        t = Output_Subtable()
        ret = t._get_visible_hijack_date()

        #assert ret[AS_Types.COLLATERAL] == #?
        #assert ret[AS_Types.ADOPTING] == #?

    def test_get_control_plane_data(self):
        """i guess these are also counts"""
        pass
