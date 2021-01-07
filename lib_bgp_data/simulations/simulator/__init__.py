#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This folder can run attack/defend scenarios for the internet"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .attacks import Attack
from .attacks import Subprefix_Hijack
from .attacks import Prefix_Hijack
from .attacks import Prefix_Superprefix_Hijack
from .attacks import Unannounced_Prefix_Hijack
from .attacks import Unannounced_Subprefix_Hijack
from .attacks import Unannounced_Prefix_Superprefix_Hijack

from .attacks import Naive_Origin_Hijack
from .attacks import Intermediate_AS_Hijack_1
from .attacks import Intermediate_AS_Hijack_2
from .attacks import Intermediate_AS_Hijack_3
from .attacks import Intermediate_AS_Hijack_4
from .attacks import Intermediate_AS_Hijack_5

from .simulator import Simulator
