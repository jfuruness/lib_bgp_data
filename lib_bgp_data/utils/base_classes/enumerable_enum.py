#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains Enumerable_Enum"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from enum import Enum

class Enumerable_Enum(Enum):
    """Simply an enum class that easily lists values"""

    # https://stackoverflow.com/a/54919285
    @classmethod
    def list_values(cls):
        """Lists the values of an enum, useful in some cases"""

        return list(map(lambda c: c.value, cls))
