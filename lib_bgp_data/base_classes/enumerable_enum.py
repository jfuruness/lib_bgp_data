#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains Enumerable_Enum"""

from enum import Enum

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Enumerable_Enum(Enum):
    # https://stackoverflow.com/a/54919285
    @classmethod
    def list_values(cls):
        return list(map(lambda c: c.value, cls))
