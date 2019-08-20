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


# enum because strings shouldn't just be being passed around
# This is for all the policies
class Policies(Enum):
    """The three types of routing policies"""

    BGP = "bgp"
    ROV = "rov"
    ROVPP = "rovpp"
    ROVPPFP = "rovppb"
    ROVPPF = "rovppbp"
# This creates an enum that is for non bgp policies
non_bgp_policies_dict = {x[0]: x[1].value
                         for x in Policies.__members__.items()
                         if x[1].value != Policies.BGP.value}
Non_BGP_Policies = Enum('Non_BGP_Policies', non_bgp_policies_dict)

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

    BLACKHOLED = "blackholed"
    NOT_BLACKHOLED_HIJACKED = "hijacked"
    NOT_BLACKHOLED_NOT_HIJACKED = "not_hijacked"
