#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from enum import Enum

from ..enums import Policies

from ...utils.base_classes import Enumerable_Enum

class Measurement_Types(Enum):
    DATA_PLANE_HIJACKED = "trace_hijacked_{}"
    DATA_PLANE_DISCONNECTED = "trace_disconnected_{}"
    DATA_PLANE_SUCCESSFUL_CONNECTION = "trace_connected_{}"
    CONTROL_PLANE_HIJACKED = "c_plane_hijacked_{}"
    CONTROL_PLANE_DISCONNECTED = "c_plane_disconnected_{}"
    CONTROL_PLANE_SUCCESSFUL_CONNECTION = "c_plane_connected_{}"
    HIDDEN_HIJACK_VISIBLE_HIJACKED = "visible_hijacks_{}"
    HIDDEN_HIJACK_HIDDEN_HIJACKED = "hidden_hijacks_{}"
    HIDDEN_HIJACK_ALL_HIJACKED = "trace_hijacked_{}"


class Graph_Formats(Enum):
    PNG = ".png"
    TIKZ = ".tex"

class Policy_Combos(Enumerable_Enum):
    # The various subsets of policies that get graphed
    ALL = list(Policies.__members__.values())
    ROVPP = [Policies.BGP,
             Policies.ROV,
             Policies.ROVPP_V1,
             Policies.ROVPP_V2,
             Policies.ROVPP_V2_AGGRESSIVE,
             Policies.ROVPP_V3]
    ROVPP_LITE = [Policies.BGP,
                  Policies.ROV,
                  Policies.ROVPP_V1_LITE,
                  Policies.ROVPP_V2_LITE,
                  Policies.ROVPP_V2_AGGRESSIVE_LITE,
                  Policies.ROVPP_V3_LITE]
    ROVPP_LITE_COMPARISON = [Policies.ROVPP_V1,
                             Policies.ROVPP_V1_LITE,
                             Policies.ROVPP_V2,
                             Policies.ROVPP_V2_LITE,
                             Policies.ROVPP_V3,
                             Policies.ROVPP_V3_LITE]
    EZ_BGP_SEC = [Policies.BGP,
                  Policies.EZ_BGP_SEC_DIRECTORY_ONLY,
                  Policies.EZ_BGP_SEC_COMMUNITY_DETECTION_LOCAL,
                  Policies.EZ_BGP_SEC_COMMUNITY_DETECTION_GLOBAL,
                  Policies.EZ_BGP_SEC_COMMUNITY_DETECTION_GLOBAL_LOCAL,
                  Policies.BGPSEC]
