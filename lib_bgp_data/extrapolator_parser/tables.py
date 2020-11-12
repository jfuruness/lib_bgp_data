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

from ..database import Generic_Table
from ..rovpp.enums import Attack_Types, Data_Plane_Conditions

class ROVPP_Extrapolator_Rib_Out_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "rovpp_extrapolator_rib_out"

    def fill_table(self, attack_type):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        logging.debug("Creating rovpp ribs out table")

        sql = f"""CREATE UNLOGGED TABLE {self.name} AS (
              SELECT exr1.asn, exr1.prefix, exr1.origin, exr1.received_from_asn,
                     exr1.time, exr1.alternate_as, exr1.opt_flag
                FROM rovpp_extrapolation_results exr1
                LEFT JOIN rovpp_extrapolation_results exr2
                    ON exr1.asn = exr2.asn AND exr1.prefix >> exr2.prefix
                WHERE exr2.asn IS NULL);"""
        self.execute(sql)


        # Do this to more efficiently keep track of leak info
        if attack_type == Attack_Types.LEAK:
            assert False, "Not yet implimented"
            # CHANGE LATER
            attacker = self.execute("""SELECT asn FROM tracked_ases
                                    WHERE attacker=TRUE""")[0]["asn"]
            sql = f"""UPDATE {self.name}
                    SET received_from_asn = 
                    {Data_Plane_Conditions.HIJACKED.value}
                    WHERE asn = {attacker};"""
            self.execute(sql)
