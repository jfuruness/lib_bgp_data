#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains enums placed here to avoid circular imports"""

from enum import Enum

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Hijack_Types(Enum):

    SUBPREFIX_HIJACK = "subprefix_hijack"
    PREFIX_HIJACK = "prefix_hijack"
    NO_COMPETING_ANNOUNCEMENT_HIJACK = "no_competing_announcement_hijack"

# enum because strings shouldn't just be being passed around
# This is for all the policies
class Policies(Enum):
    """The three types of routing policies"""

    BGP = 0
    ROV = 1
    ROVPP = 2
    ROVPPB = 3
    ROVPPBP = 4
# This creates an enum that is for non bgp policies
_non_bgp_policies_dict = {x[0]: x[1].value
                         for x in Policies.__members__.items()
                         if x[1].value != Policies.BGP.value}
Non_BGP_Policies = Enum('Non_BGP_Policies', _non_bgp_policies_dict)

########################
### Statistics Enums ###
########################

class Planes(Enum):
    """The two types of data planes"""


    # This uses the last hop and checks if recieved hijack
    DATA_PLANE = "data_plane"
    # This checks if recieved hijack
    CONTROL_PLANE = "control_plane"

class Conditions(Enum):

    BHOLED = 64512
    HIJACKED = 64513
    NOTHIJACKED = 64514
    PREVENTATIVEHIJACKED = 64515
    PREVENTATIVENOTHIJACKED = 64516

class Control_Plane_Conditions(Enum):
    RECEIVED_ATTACKER_PREFIX_ORIGIN = "received_attacker_prefix_origin"
    RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN = "recieved_only_victim_prefix_origin"
    RECEIVED_BHOLE = "received_blackhole"
    NO_RIB = "no_rib"
