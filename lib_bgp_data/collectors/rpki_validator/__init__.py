#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains RPKI Validator functionality

The purpose of this class is to obtain the validity data for all of the
prefix origin pairs in our announcements data, and insert it into a
database. This is done through a series of steps, detailed on README.
"""


__authors__ = ["Justin Furuness", "Cameron Morris"]
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .rpki_validator_parser import RPKI_Validator_Parser
from .rpki_validator_wrapper import RPKI_Validator_Wrapper
