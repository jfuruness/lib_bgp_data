#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains enums for possible sources of MRT Files"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from enum import Enum

class MRT_Sources(Enum):

    RIPE = "ripe"
    ROUTE_VIEWS = "route_views"
    ISOLARIO = "isolario"
