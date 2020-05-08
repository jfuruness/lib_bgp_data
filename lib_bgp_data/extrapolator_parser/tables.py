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
from ..rovpp.tables import Attackers_Table, Victims_Table

class ROVPP_Extrapolator_Rib_Out_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    name = "rovpp_extrapolator_rib_out"

    def fill_table(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        logging.debug("Creating rovpp ribs out table")

        # Could be written as massive SQL,
        # But this is easier to read and debug

        more_specific_results_table = "rovpp_exr_more_specific"
        less_specific_results_table = "rovpp_exr_less_specific"
        only_victim_results_table = "rovpp_exr_only_victim"

        outputs = [more_specific_results_table, less_specific_results_table]
        inputs = [Attackers_Table.name, Victims_Table.name]
        for input_name, output_name in zip(inputs, outputs):
            self.execute(f"DROP TABLE IF EXISTS {output_name}")
            # First we get the more and less specific prefix tables
            sql = f"""CREATE UNLOGGED TABLE {output_name} AS (
                  SELECT rovpp.asn, rovpp.prefix,
                     rovpp.origin, rovpp.received_from_asn
                          FROM rovpp_extrapolation_results rovpp
                  INNER JOIN {input_name} input_table
                      ON input_table.prefix = rovpp.prefix);"""
            self.execute(sql)
        # Now we can get all the less specific prefixes that do not have
        # a corresponding prefix in the more specific prefixes
        # In other words, asn only recieved victim prefix
        self.execute(f"DROP TABLE IF EXISTS {only_victim_results_table}")
        sql = f"""CREATE UNLOGGED TABLE {only_victim_results_table} AS (
                SELECT a.asn, a.prefix, a.origin, a.received_from_asn
                    FROM {less_specific_results_table} a
                LEFT JOIN {more_specific_results_table} b
                    ON b.asn = a.asn AND b.prefix << a.prefix
                WHERE b.asn IS NULL);"""
        self.execute(sql)
        # Now that we have more specific and less specific prefix table,
        # Simply perform a union
        # Note that this isn't the fastest way to do it
        # We could use subqueries. But those are hard to read
        # And if we propogate everything at once, it doesn't matter
        self.execute(f"DROP TABLE IF EXISTS rovpp_extrapolator_rib_out")
        sql = f"""CREATE UNLOGGED TABLE rovpp_extrapolator_rib_out AS (
              SELECT * FROM {more_specific_results_table}
              UNION
              SELECT * FROM {only_victim_results_table});"""
        self.execute(sql)

        # Delete all unnessecary tables
        for table_name in [more_specific_results_table,
                           less_specific_results_table,
                           only_victim_results_table]:
            self.execute(f"DROP TABLE {table_name}")

        logging.debug("Rovpp ribs out completed")
