#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROAs Collector

The purpose of this class is to download ROAs from rpki and insert them
into a database. For detailed instructions see README.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Xinyu"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .roas_parser import ROAs_Parser, ROAs_Collector
