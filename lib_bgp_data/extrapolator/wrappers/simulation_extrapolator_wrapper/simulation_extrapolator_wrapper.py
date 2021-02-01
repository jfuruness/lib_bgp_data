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

import psycopg2

from .tables import Simulation_Extrapolator_Results_Table
from .tables import Simulation_Extrapolator_Forwarding_Table

from ..extrapolator_wrapper import Extrapolator_Wrapper

from ....collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table
from ....utils.base_classes import Parser
from ....utils.database import Database
from ....utils import utils


class Simulation_Extrapolator_Wrapper(Extrapolator_Wrapper):
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = []

    branch = "rovpp_compat_modifications"

    def _run(self,
             table_names,
             rounds,
             extra_bash_arg_1,
             extra_bash_arg_2,
             extra_bash_arg_3,
             extra_bash_arg_4,
             extra_bash_arg_5,
             exr_bash=None,
             attack=None):
        """Runs the bgp-extrapolator and verifies input.

        Installs if necessary. See README for in depth instructions.
        """

        logging.debug("About to run the simulation extrapolator")

        v = "" if "ez_bgp" in self.__class__.__name__.lower() else "-v 1"
        # Default bash args
        default_bash_args = f"{self.install_location} {v} "
        # Added for ezbgpsec but should work for all
        default_bash_args += f"-i 0 -b 0 -a {MRT_W_Metadata_Table.name} "
        default_bash_args += "".join(f" -t {x}" for x in table_names)
        default_bash_args += f" --rounds {rounds} "

        default_bash_args = self.append_extra_bash_args(default_bash_args,
                                                        extra_bash_arg_1,
                                                        extra_bash_arg_2,
                                                        extra_bash_arg_3,
                                                        extra_bash_arg_4,
                                                        extra_bash_arg_5)
        #input("\n" * 10 + default_bash_args + "\n" * 10)
        logging.debug(default_bash_args)

        for _round in range(1, rounds + 1):
            # Clear db before run so it errors properly
            with Simulation_Extrapolator_Results_Table(clear=True,
                                                       round_num=_round) as _:
                pass

        # Exr bash here for dev only. If set override default args
        # Timeout set to 20 minutes. Normally it runs in a few seconds
        utils.run_cmds(exr_bash if exr_bash else default_bash_args, timeout=1800)

        for _round in range(1, rounds + 1):
            with Simulation_Extrapolator_Results_Table(round_num=_round) as db:
                try:
                    assert db.get_count() > 0
                except (AssertionError, psycopg2.errors.UndefinedTable):
                    raise Exception("Extrapolator didn't populate")

            # Gets forwarding tables. Basically returns only more specific prefixes
            with Simulation_Extrapolator_Forwarding_Table(clear=True,
                                                          round_num=_round) as _db:
                logging.debug("Extrapolation complete, writing ribs out tables")
                _db.fill_table(attack)
                _db.execute(f"ANALYZE {_db.name}")

    def append_extra_bash_args(self, bash, arg_1, arg_2, arg_3, arg_4, arg_5):
        return bash
