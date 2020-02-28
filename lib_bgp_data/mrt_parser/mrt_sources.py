#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains enums for possible sources of MRT Files"""

from ..base_classes import Enumerable_Enum

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class MRT_Sources(Enumerable_Enum):

    RIPE = "ripe"
    ROUTE_VIEWS = "route_views"
    ISOLARIO = "isolario"
