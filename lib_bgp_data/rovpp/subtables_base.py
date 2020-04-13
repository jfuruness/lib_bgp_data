#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains the base class subtables

Used for splitting the input/output into separate tables
so that we can get data on different parts of the internet
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .tables import Top_100_ASes_Table, Edge_ASes_Table, Etc_ASes_Table


class Subtables:

    def __init__(self, percents, connect=True):

        # Note that if you want to change adoption percentage:
        # Simply change percents to a list of your choosing here

        # Add any extra tables to this initial list
        self.tables = [Subtable(Top_100_ASes_Table,
                                percents,
                                possible_attacker=False),
                       Subtable(Edge_ASes_Table, percents)]
        # Etc table must go at the end. It is all leftover ases
        self.tables.append(Subtable(Etc_ASes_Table,
                                    percents,
                                    possible_attacker=False))

        if connect:
            for table in self.tables:
                table.connect()

    def close(self):
        for table in self.tables:
            table.close()


class Subtable:
    """Subtable that we divide results into"""

    def __init__(self, Table_Class, percents, possible_attacker=True):
        self.Table = Table_Class
        self.possible_attacker = possible_attacker
        self.percents = percents

    def connect(self):
        """Connects table to database"""

        self.Table = self.Table()

    def close(self):
        """Closes connection"""

        self.Table.close()
