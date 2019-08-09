#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator_Inverse_Results_Table

Extrapolator_Inverse_Results_Table inherits from Database. The Database
class allows for the conection to a database upon initialization. The
class can create an index for use by the what if analysis.

Possible future improvements:
    -Add test cases
"""

from ..utils import Database, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Extrapolator_Inverse_Results_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    @error_catcher()
    def create_index(self):
        """Creates index."""

        sql = """CREATE INDEX ON extrapolation_inverse_results
                 USING GIST(prefix inet_ops, origin);""" 
        self.cursor.execute(sql)
