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
from .input_subtables import Input_Subtables, Input_Subtable
from .output_subtables import Output_Subtables, Output_Subtable


# This is probably not the best way to do this inheritance,
# But they are all kind of messy anyways so whatever
class Subtables(Input_Subtables, Output_Subtables):

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

    def fill_tables(self):
        self.possible_attackers = []
        for table in self.tables:
            table.Input_Table.fill_table(self.names)
            table.ases = set([x["asn"] for x in table.Input_Table.get_all()])
            self.possible_attackers.extend(table.ases if table.possible_attacker else [])

    def close(self):
        for table in self.tables:
            table.close()

    @property
    def names(self):
        return [x.table.name for x in self.tables]

class Subtable(Input_Subtable, Output_Subtable):
    """Subtable that we divide results into"""

    def __init__(self, Table, percents, possible_attacker=True, policy=None):
        self.table = Table
        self.possible_attacker = possible_attacker
        self.percents = percents
        self.permanent_policy = policy

    def connect(self):
        """Connects table to database"""

        self.Input_Table = self.table(clear=True)
        self.Rib_Out_Table = self.Input_Table.Rib_Out_Table(clear=True)

    def close(self):
        """Closes connection"""

        self.Input_Table.close()
        self.Rib_Out_Table.close()
