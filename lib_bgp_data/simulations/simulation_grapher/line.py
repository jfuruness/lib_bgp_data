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

    def add_data(self, attr_combo_dict, x_attrs, x_axis_col, graph_type):
        """results consists of lits of RealDictRows from db

        This adds db data to the line to be graphed
        """

        results = None
        with Simulation_Results_Avg_Table() as db:
            sql = f"""SELECT * FROM {db.name}
                  WHERE """
            for col_name, col_val in attr_combo_dict.items():
                if isinstance(col_val, int):
                    sql += f"{col_name} = {col_val}"
                elif isinstance(col_val, str):
                    sql += f"{col_name} = '{col_val}'"
                elif col_val is None:
                    sql += f"{col_name} IS NULL"
                else:
                    print(col_name, col_val)
                    assert False, "improper column value"
                sql += " AND "
            sql += f"adopt_pol = '{self.policy}'"
            # Gets the name
            sql += f" ORDER BY {x_axis_col}"
            # Gets the list of potential x values
            results = [x for x in db.execute(sql)
                       if x[x_axis_col] in x_attrs]
        for result in results:
            self.x.append(int(result[x_axis_col]))
            self.y.append(float(result[graph_type]) * 100)
            self.yerr.append(float(result[graph_type + "_confidence"]) * 100)

    def fmt(self, line_formatter):
        return line_formatter.get_format_kwargs(self.policy)
