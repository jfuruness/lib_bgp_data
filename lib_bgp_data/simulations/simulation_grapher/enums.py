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
