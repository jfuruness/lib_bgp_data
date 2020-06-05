#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Hijack_End_Time_Parser

The purpose of this class is to download the end times for hijack events
into a database. This is done through a series of steps.

Read README for in depth explanation.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from datetime import datetime
import logging
from subprocess import check_output, STDOUT, DEVNULL

from ..base_classes import Parser
from ..utils import utils


class Hijack_End_Time_Parser(Parser):
    """This class downloads, parses, and deletes files from Caida.

    In depth explanation at the top of module.
    """

    __slots__ = []

    def __init__(self, **kwargs):
        """Initializes logger and path variables."""

        super(Hijack_End_Time_Parser, self).__init__(**kwargs)
#        if not os.path.exists("/usr/bin/bgpscanner"):
#            logging.warning("Dependencies are not installed. Installing now.")
#            MRT_Installer.install_dependencies()

    def _run(self, *args):
        """doc later"""

        
