#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This subpackage contains the functionality to parse MRT files.

The purpose of this subpackage is to download the mrt files and insert them
into a database. See README for detailed explanation.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

from .mrt_metadata import MRT_Metadata_Parser
from .mrt_base import MRT_Parser, MRT_Sources
