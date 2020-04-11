#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator

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

from ..base_classes import Parser
from ..database import Database
from ..relationships_parser.tables import Peers_Table, Provider_Customers_Table
from ..utils import utils


class Extrapolator_Parser(Parser):
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = []

    default_results_table = "exr_results"
    default_depref_table = "exr_results_depref"
    install_location = "/usr/bin/bgp-extrapolator"
    branch = None

    def _run(self, input_table="filtered_mrt_announcements"):
        """Runs the bgp-extrapolator and verifies input.

        Installs if necessary. See README for in depth instructions.
        """

        self._input_validation([input_table])

        logging.info("About to run the forecast extrapolator")

        # People who are in charge of extrapolator need to change this
        bash_args = ("bgp-extrapolator"
                     f" -a {input_table}"
                     f" -r {Extrapolator.default_results_table}"
                     f" -d {Extrapolator.default_depref_table}")
        utils.run_cmds(bash_args)

    def _input_validation(self, input_tables: list):
        """Validates proper tables exist and exr is installed"""

        logging.debug("Validating install")
        if not os.path.exists(Extrapolator.install_location):
            self.install()

        logging.debug("Validating table exist that extrapolator needs")
        with Database() as db:
            sql = "SELECT * FROM {} LIMIT 1;"

            for input_table in input_tables:
                assert len(db.execute(sql.format(input_table))) > 0,\
                    f"{input_table} is empty and is necessary for extrapolator"

            for table in [Peers_Table.name, Provider_Customers_Table.name]:
                if len(db.execute(sql.format(table))) == 0:
                    Relationships_Parser.run(**self.kwargs)
                    break

#########################
### Install Functions ###
#########################

    @utils.delete_files("BGPExtrapolator/")
    def install(self):
        """Installs extrapolator and dependencies"""

        logging.warning("It appears that the extrapolator is not installed.")
        logging.warning("Installing extrapolator now")
        self._install_dependencies()
        self._install_extrapolator()

    def _install_dependencies(self):
        """Installs dependencies that the extrapolator needs"""

        bash_args = ("sudo apt install -y "
                     "build-essential "
                     "make "
                     "libboost-dev "
                     "libboost-test-dev "
                     "libboost-program-options-dev "
                     "libpqxx-dev "
                     "libboost-filesystem-dev "
                     "libboost-log-dev "
                     "libboost-thread-dev "
                     "libpq-dev")
        utils.run_cmds(bash_args)


    def _install_extrapolator(self):
        """Installs extrapolator and moves it to /usr/bin"""

        cmds = ["git clone https://github.com/c-morris/BGPExtrapolator.git",
                "cd BGPExtrapolator"]
        # Sometimes dev team moves stuff to other branches
        if self.branch:
            cmds += [f"git checkout -b {self.branch} origin/{self.branch}"]

        cmds += [f"make -j{cpu_count()}",
                 "sudo make install",
                 f"cp bgp-extrapolator {self.install_location}"]

        utils.run_cmds(cmds)
