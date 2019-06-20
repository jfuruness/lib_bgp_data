#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator

The purpose of this class is to run the extrapolator.
For more info see: https://github.com/c-morris/BGPExtrapolator
"""

from subprocess import check_call, DEVNULL
from ..utils import Config, error_catcher, utils, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Extrapolator:
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)

    @error_catcher()
    @utils.run_parser()
    def run_forecast(self):
        pass

    @error_catcher()
    @utils.run_parser()
    def run_rovpp(self, attacker_asn, victim_asn, expected_prefix,
                  quiet=True):
        """Runs extrapolator with a subprefix hijack"""

        self.logger.info("About to run the rovpp extrapolator")
        # Run the extrapolator
        bash_args = "rovpp-extrapolator "
        # Don't invert the results so that we have the last hop
        bash_args += "--invert-results=0 "
        # Gives the attacker asn
        bash_args += "--attacker_asn={} ".format(attacker_asn)
        # Gives the victim asn
        bash_args += "--victim_asn={} ".format(victim_asn)
        # Gives the more specific prefix that the attacker sent out
        bash_args += "--victim_prefix={}".format(expected_prefix)
        self.logger.info("Caling extrapolator with:\n{}".format(bash_args)) 
        if quiet:
            check_call(bash_args, stdout=DEVNULL, shell=True)
        else:
            check_call(bash_args, shell=True)
        
        self.logger.debug("Done running the rovpp extrapolator")
