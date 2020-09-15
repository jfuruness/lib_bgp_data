#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains test for a specific data point
See README for in depth instructions
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

# Done this way to fix circular imports
from .. import extrapolator_parser as exr
from ..utils.logger import config_logging

class Test:
    """Test class that defines a specific scenario to be run"""

    def __init__(self, scenario, attack, adopt_policy, subtables):
        """Saves the test information"""

        self.scenario = scenario
        self.attack = attack
        self.adopt_policy = adopt_policy
        self.tables = subtables

    def run(self, subtables, exrbash, exr_kwargs, percent, p_iter, pbars):
        """Simulates a test:
        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.scenario, self.adopt_policy, percent, self.attack)
        # Changes routing policies for all subtables
        subtables.change_routing_policies(self.adopt_policy)

        old_log_level = None
        # Change logging level of exr to suppress output
        if exr_kwargs.get("stream_level") in [None, logging.INFO]:
            olg_log_level = exr_kwargs.get("stream_level")
            config_logging(logging.ERROR,
                           exr_kwargs.get("section"),
                           reconfigure=True)
            
        # Runs the rov++ extrapolator
        exr.ROVPP_Extrapolator_Parser(**exr_kwargs)._run(self.tables.names,
                                                         exr_bash=exrbash,
                                                         attack_type=self.scenario)

        pbars.update_extrapolator()

        if old_log_level is not None:
            config_logging(old_log_level,
                           exr_kwargs.get("section"),
                           reconfigure=True)


        # Stores the run's data
        subtables.store(self.attack,
                        self.scenario,
                        self.adopt_policy,
                        percent,
                        p_iter)
