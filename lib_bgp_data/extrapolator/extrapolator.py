#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator

The purpose of this class is to run the extrapolator.
For more info see: https://github.com/c-morris/BGPExtrapolator
For the specifics on how the extrapolator is run see each function
"""

from subprocess import check_call, DEVNULL
from .tables import Extrapolator_Inverse_Results_Table
from ..utils import error_catcher, utils, db_connection
# Justin globals are bad yah you know what else is bad? the logging
# module that deadlocks upon import
DEBUG = 10

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Extrapolator:
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = ['path', 'csv_dir', 'logger']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)

    @error_catcher()
    @utils.run_parser()
    def run_forecast(self, input_table=None):
        self.logger.info("About to run the forecast extrapolator")
        bash_args = "forecast-extrapolator"
        if input_table:
            bash_args += " -a {}".format(input_table)
        if self.logger.level == DEBUG:
            check_call(bash_args, shell=True)
        else:
            check_call(bash_args, stdout=DEVNULL, stderr=DEVNULL, shell=True)
        self._create_index()

    @error_catcher()
    def _create_index(self):
        self.logger.info("Creating index on the extrapolation results")
        with db_connection(Extrapolator_Inverse_Results_Table,
                           self.logger) as db:
            db.create_index()

    @error_catcher()
    @utils.run_parser()
    def run_rovpp(self, attacker_asn, victim_asn, expected_prefix, table_names):
        """Runs extrapolator with a subprefix hijack."""

        self.logger.debug("About to run the rovpp extrapolator")
        # Run the extrapolator
        bash_args = "rovpp-extrapolator "
        # Don't invert the results so that we have the last hop
        bash_args += "--invert-results=0 "
        # Gives the attacker asn
        bash_args += "--attacker_asn={} ".format(attacker_asn)
        # Gives the victim asn
        bash_args += "--victim_asn={} ".format(victim_asn)
        # Gives the more specific prefix that the attacker sent out
        bash_args += "--victim_prefix={} ".format(expected_prefix)
        bash_args += "--rovpp_ases_tables {}".format(" ".join(table_names))
        self.logger.debug("Caling extrapolator with:\n{}".format(bash_args))
        if self.logger.level == DEBUG:
            check_call(bash_args, shell=True)
        else:
            check_call(bash_args, stdout=DEVNULL, stderr=DEVNULL, shell=True)
