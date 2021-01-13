#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains Table classes

See the Database section in readme to understand how they work 
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from ....utils.database import Generic_Table

class Simulation_Extrapolator_Results_Table(Generic_Table):
    """Contains output for extrapolator results"""

    __slots__ = ["round_num"]

    def __init__(self, *args, **kwargs):
        self.round_num = kwargs.get("round_num")
        super(Simulation_Extrapolator_Results_Table,
              self).__init__(*args, **{x: y for x, y in kwargs.items()
                                       if x != "round_num"})

    @property
    def name(self):
        return "simulation_extrapolation_results_raw_round_{}".format(self.round_num)


class Simulation_Extrapolator_Forwarding_Table(Generic_Table):
    """Class with database functionality. Returns forwarding tables.

    In depth explanation at the top of the file."""

    __slots__ = ["round_num"]

    def __init__(self, *args, **kwargs):
        self.round_num = kwargs.get("round_num")
        super(Simulation_Extrapolator_Forwarding_Table,
              self).__init__(*args, **{x: y for x, y in kwargs.items()
                                       if x != "round_num"})


    @property
    def name(self):
        return "simulation_extrapolator_forwarding_round_{}".format(self.round_num)

    def fill_table(self, attack_type):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        logging.debug("Creating rovpp ribs out table")

        with Simulation_Extrapolator_Results_Table(round_num=self.round_num) as db:
            sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
                   SELECT exr1.*
                    FROM {db.name} exr1
                    LEFT JOIN {db.name} exr2
                        ON exr1.asn = exr2.asn AND exr1.prefix >> exr2.prefix
                    WHERE exr2.asn IS NULL);"""
            self.execute(sql)
