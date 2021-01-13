#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This folder contains all the different attacks that can be run"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .attack import Attack
from .attack_classes import Subprefix_Hijack
from .attack_classes import Prefix_Hijack
from .attack_classes import Prefix_Superprefix_Hijack
from .attack_classes import Unannounced_Prefix_Hijack
from .attack_classes import Unannounced_Subprefix_Hijack
from .attack_classes import Unannounced_Prefix_Superprefix_Hijack

from .attack_classes import Naive_Origin_Hijack
from .attack_classes import Intermediate_AS_Hijack_1
from .attack_classes import Intermediate_AS_Hijack_2
from .attack_classes import Intermediate_AS_Hijack_3
from .attack_classes import Intermediate_AS_Hijack_4
from .attack_classes import Intermediate_AS_Hijack_5
