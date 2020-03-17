#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains enum Event_Types

This class contains the event types in the bgpstream.com website.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from ..base_classes import Enumerable_Enum

class Event_Types(Enumerable_Enum):
    """Possible bgpstream.com event types"""

    HIJACK = "Possible Hijack"
    LEAK = "BGP Leak"
    OUTAGE = "Outage"
