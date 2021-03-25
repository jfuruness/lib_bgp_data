#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from ..subtables_base import Subtables, Subtable
from ..tables import Top_100_ASes_Table
#from ..input_subtables import Input_Subtables, Input_Subtable
from ...attacks import Subprefix_Hijack
from ....enums import Policies
from .....utils.database import Database
from .....collectors import Relationships_Parser, AS_Rank_Website_Parser

class Test_Input_Subtables:
    """Subtable inherits from Input_Subtable and Output_Subtable for code reuse"""

    table = Top_100_ASes_Table
    percents = [5]

    @pytest.fixture(scope="class")
    def subtable(self):
        Relationships_Parser().run()
        AS_Rank_Website_Parser().run()
        #subtable.connect()
        return Subtable(self.table, self.percents)

    def test_set_adopting_ases(self, subtable):
        """Check the correct number of ases adopt???"""
        iteration_num = 0
        attack = Subprefix_Hijack(55, 66)
        random_seed = 1

        subtable.connect()
        subtable.set_adopting_ases(iteration_num, attack, self.table.name, random_seed)

        percent = self.percents[iteration_num]

        # ._.
        select_asns = f"SELECT DISTINCT asn FROM {subtable.table.name};"
        select_impliments = f"SELECT * FROM {subtable.table.name} WHERE impliment = TRUE;"

        with Database() as db:
            assert len(db.execute(select_impliments)) ==  len(db.execute(select_asns)) * percent // 100

    def test_change_routing_policies(self, subtable):
        """Change policy if it's not permanent"""
        # need to set some impliments to true first
        self.test_set_adopting_ases(subtable)

        for policy in Policies:
            subtable.change_routing_policies(policy)

            sql = f"SELECT * FROM {subtable.table.name} WHERE as_type = {policy.value}"
            with Database() as db:
                assert len(db.execute(sql)) > 0

    def test_get_possible_attackers(self, subtable):
        """Returns all ASNs in the table if possible attacker is True,
            else returns an empty list."""

        _table = self.table()
        _table.fill_table()
        # the self.Input_Table attribute gets set in the connect method
        subtable.connect()
        assert len(subtable.get_possible_attackers()) == _table.get_count()
        subtable.possible_attacker = False
        assert subtable.get_possible_attackers() == []

