#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module runs the ROAs Collector.

The ROAs Collector gets all the signed and validated roas and stores
them into a database. For more extensive documentation, see __init__.py
"""


from .roas_collector import ROAs_Collector

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def main():
    ROAs_Collector().parse_roas()
