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


class Test:
    """Test class that defines a specific scenario to be run"""

    def __init__(self,
                 attack,
                 number_of_attackers,
                 adopt_policy,
                 subtables,
                 percent,
                 p_iter,
                 extra_bash_arg_1,
                 extra_bash_arg_2,
                 extra_bash_arg_3,
                 extra_bash_arg_4,
                 extra_bash_arg_5):
        """Saves the test information"""

        self.attack = attack
        self.number_of_attackers = number_of_attackers
        self.adopt_pol = adopt_policy
        self.tables = subtables
        self.percent = percent
        # Percent iteration
        self.p_iter = p_iter
        self.extra_bash_arg_1 = extra_bash_arg_1
        self.extra_bash_arg_2 = extra_bash_arg_2
        self.extra_bash_arg_3 = extra_bash_arg_3
        self.extra_bash_arg_4 = extra_bash_arg_4
        self.extra_bash_arg_5 = extra_bash_arg_5

    def run(self, pbars, rounds, exr_bash=None, exr_kwargs=None, exr_cls=None):
        """Simulates a test:
        the scenario is usually an attack type, Ex: subprefix hijack
        the adopt policy is the policy that (percent) percent of the internet
        deploy, for example, BGP, ROV, etc
        """

        # Sets description with this tests info
        pbars.set_desc(self.adopt_pol,
                       self.percent,
                       self.attack,
                       self.extra_bash_arg_1,
                       self.extra_bash_arg_2,
                       self.extra_bash_arg_3,
                       self.extra_bash_arg_4,
                       self.extra_bash_arg_5)
        # Changes routing policies for all subtables
        self.tables.change_routing_policies(self.adopt_pol)

        # Runs the rov++ extrapolator
        exr_cls(**exr_kwargs)._run(self.tables.names,
                                   rounds,
                                   self.extra_bash_arg_1,
                                   self.extra_bash_arg_2,
                                   self.extra_bash_arg_3,
                                   self.extra_bash_arg_4,
                                   self.extra_bash_arg_5,
                                   exr_bash=exr_bash,
                                   attack=self.attack)

        pbars.update_extrapolator()

        for round_num in range(1, rounds + 1):
            # Stores the run's data
            self.tables.store(self.attack,
                              self.number_of_attackers,
                              self.adopt_pol,
                              self.percent,
                              self.p_iter,
                              round_num,
                              self.extra_bash_arg_1,
                              self.extra_bash_arg_2,
                              self.extra_bash_arg_3,
                              self.extra_bash_arg_4,
                              self.extra_bash_arg_5)
        pbars.update()
