#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
from ..attack import Attack
from ..attack_classes import Prefix_Hijack
from ..roa import ROA
from ..rpki import RPKI
from .....utils.base_classes import ROA_Validity as Val

class Test_Attack:

    @pytest.fixture
    def attack(self):
        victim, attacker = 55, 66
        return Attack(victim, attacker)

    def test_fill_attack_victom_rows(self):
        victim, attacker = 55, 66
        attack = Prefix_Hijack(victim, attacker)

        attack._fill_attacker_victim_rows()

        expected_list = [{"prefix": attack.default_prefix,
                        "true_victim": victim,
                        "true_attacker": attacker,
                        "true_asn": victim}]

        assert attack.victim_rows == expected_list

        expected_list[0]["true_asn"] = attacker

        assert attack.attacker_rows == expected_list

    def test_rpki(self):
        roa = ROA(Attack.default_prefix, 55)
        rpki = RPKI([roa])

        assert rpki.check_ann(roa.prefix, 55) == Val.VALID.value

        # lol
        too_long = Attack.default_prefix
        too_long = too_long[:-1] + str(int(too_long[-1]) + 1)

        assert rpki.check_ann(too_long, 55) == Val.INVALID_BY_LENGTH.value
        assert rpki.check_ann(Attack.default_prefix, 66) == Val.INVALID_BY_ORIGIN.value
        assert rpki.check_ann(too_long, 66) == Val.INVALID_BY_ALL.value

        assert rpki.check_ann("0.0.0.0/0", 55) == Val.UNKNOWN.value

    @pytest.mark.curr
    def test_db_format(self):
        victim, attacker = 55, 66
        attack = Prefix_Hijack(victim, attacker)

        print(attack.victim_rows)
        print(attack.attacker_rows)
        print("*****************")
        attack._add_ids()

        print(attack.victim_rows)
        print(attack.attacker_rows)

        #attack._fill_attacker_victim_rows()
        
        # Where is the extra data added?????????
        #print(attack.asn_dict) 
        #print(attack.db_rows) 
        #print(attack.victim_rows)
        #print(attack.attacker_rows)


    def test_format(self, attack):
        """Format method should change lists to strings with curly braces"""

        announcement_dict = {"test_list": [1, 2, 3],
                            "test_numeric": 314,
                            "test_string": 'abc'}

        assert attack._format(announcement_dict, "test_list") == "{1, 2, 3}"

        # other data types should remain the same
        assert attack._format(announcement_dict, "test_numeric") == 314
        assert attack._format(announcement_dict, "test_string") == 'abc'
