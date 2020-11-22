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
import sys

import psycopg2

from .extrapolator_parser import Extrapolator_Parser
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

    branch = "rovpp_tbl_chg"

    def _run(self, table_names, exr_bash=None, attack_type=None):
        """Runs the bgp-extrapolator and verifies input.

        Installs if necessary. See README for in depth instructions.
        """

        logging.debug("About to run the rovpp extrapolator")

        # Should be moved to exr

        bash_args = f"{self.install_location} -v 1"
        for table_name in table_names:
            bash_args += f" -t {table_name}"
        with Database() as db:
            db.execute("DROP TABLE IF EXISTS rovpp_extrapolation_results")
        logging.debug(bash_args)
        # Exr bash here for dev only
        try:
            utils.run_cmds(exr_bash if exr_bash else bash_args)
        except Exception as e:
            # Must die this hard so our sim fails
            print(f"Extrapolator failed to populate rovpp_extrapolation_results: {e}")
            sys.exit(1)
        # Gets rib out. Basically returns only more specific prefixes
        with ROVPP_Extrapolator_Rib_Out_Table(clear=True) as _db:
            try:
                assert _db.get_count("SELECT COUNT(*) FROM rovpp_extrapolation_results") > 0
            except (psycopg2.errors.UndefinedTable, AssertionError):
                print("Extrapolator failed to populate rovpp_extrapolation_results")
                sys.exit(2)
                raise Exception("Extrapolator failed to populate rovpp_extrapolation_results")
            logging.info("Extrapolation complete, writing ribs out tables")
            _db.fill_table(attack_type)
