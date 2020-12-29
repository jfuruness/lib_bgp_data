#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Line_Format:
    def __init__(self, marker, style, color):
        self.marker = marker
        self.style = style
        self.color = color
