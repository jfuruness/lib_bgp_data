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

from ..utils.base_classes import Enumerable_Enum


class Policies(Enum):
    """The possible routing policies"""

    DEFAULT = 0

    ### Current policies seen on the internet ###
    BGP = 1
    ROV = 2

    ### Standard ROV++ policies ###
    ROVPP_V0 = 3
    ROVPP_V1 = 4
    # Announces to only customers
    ROVPP_V2 = 5
    # Announces according to gao rexford
    ROVPP_V2_AGGRESSIVE = 6
    ROVPP_V3 = 7

    ### LITE version of ROV++ policies ###
    ROVPP_V1_LITE = 8
    # Announces only to customers
    ROVPP_V2_LITE = 9
    # Announces according to gao rexford
    ROVPP_V2_AGGRESSIVE_LITE = 10
    ROVPP_V3_LITE = 11

    ### SHORTEN versions of standard ROV++ policies ###
    # Announces to only customers
    ROVPP_V2_SHORTEN = 12
    # Announces according to gao rexford
    ROVPP_V2_AGGRESSIVE_SHORTEN = 13
    ROVPP_V3_SHORTEN = 14

    ### SHORTEN versions of standard ROV++ LITE policies ###
    ROVPP_V1_SHORTEN_LITE = 15
    # Announces only to customers
    ROVPP_V2_SHORTEN_LITE = 16
    # Announces according to gao rexford
    ROVPP_V2_SHORTEN_AGGRESSIVE_LITE = 17
    ROVPP_V3_SHORTEN_LITE = 18

    ### SHORTEN EXPLODE versions of ROV++ policies ###
    ROVPP_V2_SHORTEN_EXPLODE = 19
    ROVPP_V3_SHORTEN_EXPLODE = 20

    ### SHORTEN EXPLODE versions of ROV++ LITE policies ###
    ROVPP_V2_SHORTEN_EXPLODE_LITE = 21
    ROVPP_V3_SHORTEN_EXPLODE_LITE = 22

    ### EZ_BGP_SEC policies ###
    EZ_BGP_SEC_DIRECTORY_ONLY = 64
    EZ_BGP_SEC_COMMUNITY_DETECTION_LOCAL = 65
    EZ_BGP_SEC_COMMUNITY_DETECTION_GLOBAL = 66
    EZ_BGP_SEC_COMMUNITY_DETECTION_GLOBAL_LOCAL = 67
    BGPSEC = 68
    BGPSEC_TRANSITIVE = 69

# This creates an enum that is for non bgp policies
_non_default_policies_dict = {x[0]: x[1].value
                              for x in Policies.__members__.items()
                              if x[1].value != Policies.DEFAULT.value}
Non_Default_Policies = Enum('Non_Default_Policies', _non_default_policies_dict)

########################
### Statistics Enums ###
########################


class Data_Plane_Conditions(Enumerable_Enum):
    """Possible outcomes from data plane conditions

    All announcements should traceback to one of these

    If it does not, the code will error

    Picked because these are reserved asn's"""

    BHOLED = 64512
    HIJACKED = 64513
    NOTHIJACKED = 64514


class Control_Plane_Conditions(Enumerable_Enum):
    """Conditions you see in the control plane"""

    RECV_ATK_PREF_ORIGIN = "received_attacker_prefix_origin"
    RECV_ONLY_VIC_PREF_ORIGIN = "recieved_only_victim_prefix_origin"
    RECV_BHOLE = "received_blackhole"
    NO_RIB = "no_rib"


class AS_Types(Enumerable_Enum):
    """Ases either adopt or don't"""

    COLLATERAL = 0
    ADOPTING = 1
    ALL = 2
