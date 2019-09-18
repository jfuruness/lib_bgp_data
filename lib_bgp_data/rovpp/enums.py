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

    SUBPREFIX_HIJACK = 0
    PREFIX_HIJACK = 1
    NO_COMPETING_ANNOUNCEMENT_HIJACK = 2

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
non_bgp_policies_dict = {x[0]: x[1].value
                         for x in Policies.__members__.items()
                         if x[1].value != Policies.BGP.value}
Non_BGP_Policies = Enum('Non_BGP_Policies', non_bgp_policies_dict)

class Top_Node_Policies(Enum):
    ROV = Policies.ROV.value
    ROVPP = Policies.ROVPP.value

########################
### Statistics Enums ###
########################

class Planes(Enum):
    """The two types of data planes"""


    # This uses the last hop and checks if recieved hijack
    DATA_PLANE = 0
    # This checks if recieved hijack
    CONTROL_PLANE = 1

class Conditions(Enum):

    BHOLED = 0  # blackholed
    HIJACKED = 1  # not blackholed hijacked
    NOTHIJACKED = 2  # "not_hijacked"
    DISCONNECTED = 3  # disconnected
