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
