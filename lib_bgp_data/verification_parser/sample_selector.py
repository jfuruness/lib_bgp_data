#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class sample_selector

See github
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from .tables import MRT_W_Monitors_Table
from .tables import Monitors_Table
from .tables import Control_Monitors_Table
from .tables import Control_Announcements_Table
from .tables import Test_Announcements_Table

class Sample_Selector:
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def select_samples(self):
        tables = [
        # Step 1:
        # Add monitor_asn to all mrt announcements
#        MRT_W_Monitors_Table,
        # Get a table of all Monitors with statistics
#        Monitors_Table,
        # Step 2:
        # Only use monitors that have rib out
        # (exr doesn't compute real rib in since it processes ann like a moment
        # in time. Won't go into detail here)
#        Control_Monitors_Table,
        # Step 3:
        # Get all announcements for prefixes that exist in all control monitors
        # Note that since we only use monitors that only output rib out
        # Each monitor only has 1 ann per prefix
#        Control_Announcements_Table,
        # Step 4:
        # Get all announcements that <<= control_announcemnt.prefixes
        # For these collectors
        Test_Announcements_Table]

        for Table in tables:
            with Table(clear=True) as db:
                db.fill_table()
