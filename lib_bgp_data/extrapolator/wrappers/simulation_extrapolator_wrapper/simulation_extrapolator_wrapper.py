#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Simulatoin_Extrapolator

The purpose of this class is to run the extrapolator
to simulate attack/defend scenarios.
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

from .tables import Simulation_Extrapolator_Results_Table
from .tables import Simulation_Extrapolator_Forwarding_Table

from ..extrapolator_wrapper import Extrapolator_Wrapper

from ....utils.base_classes import Parser
from ....utils.database import Database
from ....utils import utils


class Simulation_Extrapolator_Wrapper(Extrapolator_Wrapper):
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = []

    branch = "rovpp_tbl_chg"

    def _run(self, table_names, exr_bash=None, attack=None):
        """Runs the bgp-extrapolator and verifies input.

        Installs if necessary. See README for in depth instructions.
        """

        logging.debug("About to run the simulation extrapolator")

        # Default bash args
        default_bash_args = f"{self.install_location} -v 1 "
        default_bash_args += "".join(f" -t {x}" for x in table_names)
        logging.debug(default_bash_args)

        # Clear db before run so it errors properly
        with Simulation_Extrapolator_Results_Table(clear=True) as _:
            pass

        # Exr bash here for dev only. If set override default args
        utils.run_cmds(exr_bash if exr_bash else default_bash_args)

        with Simulation_Extrapolator_Results_Table() as db:
            assert db.get_count() > 0, "Extrapolator didn't populate results"

        # Gets forwarding tables. Basically returns only more specific prefixes
        with Simulation_Extrapolator_Forwarding_Table(clear=True) as _db:
            logging.debug("Extrapolation complete, writing ribs out tables")
            _db.fill_table(attack_type)
