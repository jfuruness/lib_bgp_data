#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class Attack.

This class is used to store information about an attack.

See README for in depth instruction
"""

__authors__ = ["Justin Furuness", "Cameron Morris"]
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import ipaddress

from .enums import Attack_Types


class Attack_Generator:
    def __init__(self):
        self.attacks = self.gen_attacks()
        self.test_index = 0

    def get_attack(self, index, policy, attacker, victim, attack_type):
        attack = self.attacks[attack_type].pop()
        attack.add_index_pol_attacker_victim(index, policy, attacker, victim)
        return attack
        
    def gen_attacks(self):
        atk_dict = {k: [] for k in Attack_Types}

        assert len(atk_dict) <= 3, "Must mod this func for more attacks"

        for i in range(0, 254, len(atk_dict)):
            for n in range(1000):  # Can go up to 16382
                # Cameron wrote prefix generation code
                # Should generate prefixes that do not overlap with each other

                # Subprefix attacks
                sub_atk_pref = ipaddress.ip_network(((i<<24) + (n<<10), 24))
                sub_vic_pref = ipaddress.ip_network(((i<<24) + (n<<10), 22))
                subprefix_atk = Attack(sub_atk_pref, sub_vic_pref)
                atk_dict[Attack_Types.SUBPREFIX_HIJACK].append(subprefix_atk)
                # Prefix attacks
                pref_atk = ipaddress.ip_network((((i+1)<<24) + (n<<10), 22))
                pref_vic = ipaddress.ip_network((((i+1)<<24) + (n<<10), 22))
                prefix_attack = Attack(pref_atk, pref_vic)
                atk_dict[Attack_Types.PREFIX_HIJACK].append(prefix_attack)
                # Non compete attacks
                non_comp_pref = ipaddress.ip_network((((i+2)<<24) + (n<<10), 22))
                non_comp = Attack(non_comp_pref)
                atk_dict[Attack_Types.UNANNOUNCED_PREFIX_HIJACK].append(non_comp)
        return atk_dict

class Attack:
    # Default for vic prefix being none is for non competing hijacks
    def __init__(self, attacker_prefix, victim_prefix=None):

        self.attacker_prefix = attacker_prefix
        self.victim_prefix = victim_prefix

    def add_index_pol_attacker_victim(self,
                                       list_index,
                                       policy,
                                       attacker_asn,
                                       victim_asn=None):
        # list_index is the place to look in the list for
        self.list_index = list_index
        self.policy = policy
        self.attacker_asn = attacker_asn
        self.victim_asn = victim_asn

    @property
    def attacker_row(self):
        return [self.attacker_prefix,
                "{" + str(self.attacker_asn) + "}",
                self.attacker_asn,
                self.list_index,
                self.policy.value]

    @property
    def victim_row(self):
        if self.victim_prefix is None:
            return None
        else:
            return [self.victim_prefix,
                    "{" + str(self.victim_asn) + "}",
                    self.victim_asn,
                    self.list_index,
                    self.policy.value]
