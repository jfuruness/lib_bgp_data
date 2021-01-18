#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator_Analyzer

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .tables import Monitors_Table, Control_Monitors_Table

from ..wrappers import Extrapolator_Wrapper

from ...collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table
from ...collectors.relationships.tables import Peers_Table
from ...collectors.relationships.tables import Provider_Customers_Table
from ...utils.base_classes import Parser
from ...utils.database import Database


class Verification_Parser(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def _run(self):
        for control_monitor_asn in []:
            for multihomed_opt in []
#                for 
        Extrapolator_Wrapper(**self.kwargs)._run()
