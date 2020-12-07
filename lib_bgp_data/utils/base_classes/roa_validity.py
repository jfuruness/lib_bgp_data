#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains ROA Validity"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from enum import Enum

class ROA_Validity(Enum):
    """ROA Validity States"""

    # NOTE: other parts rely on this ordering (worse asc).
    # DO NOT CHANGE IT!
    VALID = 0
    UNKNOWN = 1
    INVALID_BY_LENGTH = 2
    INVALID_BY_ORIGIN = 3
    INVALID_BY_ALL = 4
