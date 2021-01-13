#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains subclasses of Attack.

This class is used to store information about an attack.
Currently this only accounts for hijacks

See README for in depth instruction
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .attack import Attack


class Subprefix_Hijack(Attack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_subprefix]
    victim_prefixes = [Attack.default_prefix]


class Prefix_Hijack(Attack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix]
    victim_prefixes = [Attack.default_prefix]


class Prefix_Superprefix_Hijack(Attack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix, Attack.default_superprefix]
    victim_prefixes = [Attack.default_prefix]


class Unannounced_Hijack(Attack):
    """Should be inherited, unnanounced attacks"""

    victim_prefixes = []


class Unannounced_Prefix_Hijack(Unannounced_Hijack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix]


class Unannounced_Subprefix_Hijack(Unannounced_Hijack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix, Attack.default_subprefix]


class Unannounced_Prefix_Superprefix_Hijack(Unannounced_Hijack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix, Attack.default_superprefix]

class Naive_Origin_Hijack(Attack):

    victim_prefixes = [Attack.default_prefix]
    attacker_prefixes = [Attack.default_prefix]

    # True victim is true origin
    def _get_as_path(self, true_asn, true_victim, true_attacker):
        # Victim path
        if true_asn == true_victim:
            return [true_victim]
        # Attacker path
        else:
            return [true_attacker, true_victim]

class Intermediate_AS_Hijack_1(Attack):
 
    victim_prefixes = [Attack.default_prefix]
    attacker_prefixes = [Attack.default_prefix]

    reserved_asns = [65534, 65533, 65532, 65531, 65530]

    number_intermediate_ases = 1

    # True victim is true origin
    def _get_as_path(self, true_asn, true_victim, true_attacker):
        if true_asn == true_victim:
            return [true_victim]
        # Attacker path
        else:
            return [true_attacker] + self.reserved_asns[:self.number_intermediate_ases] + [true_victim]


class Intermediate_AS_Hijack_2(Intermediate_AS_Hijack_1):
    number_intermediate_ases = 2


class Intermediate_AS_Hijack_3(Intermediate_AS_Hijack_1):
    number_intermediate_ases = 3


class Intermediate_AS_Hijack_4(Intermediate_AS_Hijack_1):
    number_intermediate_ases = 4


class Intermediate_AS_Hijack_5(Intermediate_AS_Hijack_1):
    number_intermediate_ases = 5
