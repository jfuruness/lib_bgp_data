#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .tables import Simulation_Results_Avg_Table


class Line:
    def __init__(self, policy):
        self.policy = policy
        self.x = []
        self.y = []
        self.yerr = []

    def add_data(self, subtable, attack_type, percents, graph_type):
        """results consists of lits of RealDictRows from db

        This adds db data to the line to be graphed
        """

        with Simulation_Results_Avg_Table() as db:
            sql = f"""SELECT * FROM {db.name}
                  WHERE subtable_name = '{subtable}'
                    AND adopt_pol = '{self.policy}'
                    AND attack_type = '{attack_type}'
                  ORDER BY percent"""
            results = [x for x in db.execute(sql) if x["percent"] in percents]

        for result in results:
            self.x.append(int(result["percent"]))
            self.y.append(float(result[graph_type]) * 100)
            self.yerr.append(float(result[graph_type + "_confidence"]) * 100)

    def fmt(self, line_formatter):
        return line_formatter.get_format_kwargs(self.policy)
