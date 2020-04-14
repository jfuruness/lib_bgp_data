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

from ..extrapolator_parser import ROVPP_Extrapolator_Parser


class Test:
    def __init__(self, scenario, attack, adopt_policy, subtables):
        self.scenario = scenario
        self.attack = attack
        self.adopt_policy = adopt_policy
        self.tables = subtables

    def run(self, subtables, exrbash, exr_kwargs, percent, pbars):
        """Simulates a test:

        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.scenario, self.adopt_policy, percent, self.attack)
        # Changes routing policies for all subtables
        subtables.change_routing_policies(self.adopt_policy)
        # Runs the rov++ extrapolator
        ROVPP_Extrapolator_Parser(**exr_kwargs).run(self.tables.names, exrbash)
        # Stores the run's data
        subtables.store(self.attack, self.scenario, self.adopt_policy, percent)
