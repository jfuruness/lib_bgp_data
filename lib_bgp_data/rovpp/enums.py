#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains enums of attack/defend scenarios

See README for in depth explanation"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from enum import Enum

from ..base_classes import Enumerable_Enum
###########################
### Attack/Defend Enums ###
###########################

class Attack_Types(Enum):
    """Types of scenarios for attacks"""

    SUBPREFIX_HIJACK = "subprefix_hijack"
    PREFIX_HIJACK = "prefix_hijack"
    UNANNOUNCED_PREFIX_HIJACK = "no_competing_announcement_hijack"


class Policies(Enum):
    """The possible routing policies"""

    DEFAULT = 0
    ROV = 1
    ROVPP = 2
    ROVPPB = 3
    ROVPPBP = 4
    ROVPPBIS = 5


# This creates an enum that is for non bgp policies
_non_default_policies_dict = {x[0]: x[1].value
                              for x in Policies.__members__.items()
                              if x[1].value != Policies.DEFAULT.value}
Non_Default_Policies = Enum('Non_Default_Policies', _non_default_policies_dict)

########################
### Statistics Enums ###
########################


class Data_Plane_Conditions(Enumerable_Enum):
    """Possible outcomes from data plane conditions"""

    BHOLED = 64512
    HIJACKED = 64513
    NOTHIJACKED = 64514

class Control_Plane_Conditions(Enumerable_Enum):
    """Conditions you see in the control plane"""

    RECEIVED_ATTACKER_PREFIX_ORIGIN = "received_attacker_prefix_origin"
    RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN = "recieved_only_victim_prefix_origin"
    RECEIVED_BHOLE = "received_blackhole"
    NO_RIB = "no_rib"


class AS_Types(Enum):
    """Ases either adopt or don't"""

    NON_ADOPTING = 0
    ADOPTING = 1
