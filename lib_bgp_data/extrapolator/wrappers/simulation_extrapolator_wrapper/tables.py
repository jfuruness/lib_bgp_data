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

    __slots__ = []

    name = "rovpp_extrapolation_results"


class Simulation_Extrapolator_Forwarding_Table(Generic_Table):
    """Class with database functionality. Returns forwarding tables.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "simulation_extrapolator_forwarding"

    def fill_table(self, attack_type):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        # Fix later
        from ....simulation.enums import Attack_Types, Data_Plane_Conditions

        logging.debug("Creating rovpp ribs out table")

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
               SELECT exr1.*
                FROM {Simulation_Extrapolator_Results_Table.name} exr1
                LEFT JOIN {Simulation_Extrapolator_Results_Table.name} exr2
                    ON exr1.asn = exr2.asn AND exr1.prefix >> exr2.prefix
                WHERE exr2.asn IS NULL);"""
        self.execute(sql)
