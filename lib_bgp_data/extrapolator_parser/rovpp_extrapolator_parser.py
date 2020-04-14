#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class rovpp_Extrapolator

The purpose of this class is to run the extrapolator.
For more info see: https://github.com/c-morris/BGPExtrapolator
For the specifics on how the extrapolator is run see each function
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging
from multiprocessing import cpu_count
import os

from .extrapolator_parser import Extrapolator_Parser
from ..rovpp.tables import Attackers_Table, Victims_Table
from .tables import ROVPP_Extrapolator_Rib_Out_Table

from ..base_classes import Parser
from ..database import Database
from ..relationships_parser.tables import Peers_Table, Provider_Customers_Table
from ..utils import utils


class ROVPP_Extrapolator_Parser(Extrapolator_Parser):
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = []

    branch = "rovpp3.1.2"

    def _run(self, table_names, exr_bash=None):
        """Runs the bgp-extrapolator and verifies input.

        Installs if necessary. See README for in depth instructions.
        """

        tables = [Attackers_Table.name] + table_names
        self._input_validation(tables)

        logging.debug("About to run the rovpp extrapolator")

        bash_args = f"{self.install_location} -v 1"
        for table_name in table_names:
            bash_args += f" -t {table_name}"

        # Exr bash here for dev only
        utils.run_cmds(exr_bash if exr_bash else bash_args)

        # Gets rib out. Basically returns only more specific prefixes
        with ROVPP_Extrapolator_Rib_Out_Table(clear=True) as _db:
            _db.fill_table()
