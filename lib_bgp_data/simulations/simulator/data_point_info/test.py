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

from ... import extrapolator as exr

from ....utils.logger import config_logging

class Test:
    """Test class that defines a specific scenario to be run"""

    def __init__(self, attack, adopt_policy, subtables, percent, p_iter):
        """Saves the test information"""

        self.attack = attack
        self.adopt_pol = adopt_policy
        self.tables = subtables
        self.percent = percent
        # Percent iteration
        self.p_iter = p_iter

    def run(self, pbars, exrbash=None, exr_kwargs=None):
        """Simulates a test:
        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.adopt_policy, percent, self.attack)
        # Changes routing policies for all subtables
        self.tables.change_routing_policies(self.adopt_policy)

        # Runs the rov++ extrapolator
        exr.Simulation_Extrapolator_Wrapper(**exr_kwargs)._run(
            self.tables.names, exr_bash=exrbash, attack=self.attack)

        pbars.update_extrapolator()

        # Stores the run's data
        subtables.store(self.attack, self.adopt_pol, self.percent, self.p_iter)
        pbars.update()
