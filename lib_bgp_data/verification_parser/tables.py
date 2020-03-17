#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the tables for MRT generation for verification

These tables inherits from Database. The Database class allows for the
conection to a database upon initialization.

Possible future improvements:
    -Add test cases, docs, everything
"""

from ..database import Generic_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class MRT_Subtable_Table(Generic_Table):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = []

    def _create_tables(self):
        self.cursor.execute("""ALTER TABLE mrt_announcements
                            RENAME TO {}""".format(self.name))

    def drop_tables(self):
        self.cursor.execute("DROP TABLE {} IF EXSTS".format(self.name))


class Route_Views_Table(Generic_Table):
    """Inherits MRT_Subtable and overrides name"""

    pass

class RIPE_Table(Generic_Table):
    """Inherits MRT_Subtable and overrides name"""

    pass


class Isolario_Table(Generic_Table):
    """Inherits MRT_Subtable and overrides name"""

    pass
