#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for the averages API endpoint.

The averages API endpoint sums up the averages in all of the policies
columns, truncates them down to 2 decimal places, and returns the data.

Design Choices:
    -A separate blueprint was used for readability
"""

from flask import Blueprint
from flasgger import swag_from
from .api_utils import format_json, get_policies

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


averages_app = Blueprint("averages_app", __name__)


@averages_app.route("/averages/")
@swag_from("flasgger_docs/averages.yml")
@format_json(lambda: {"description": "Average data across all ASes"})
def averages():
    """Returns averages statistics across all ASNs for each policy"""

    sql = """SELECT TRUNC(SUM(blocked_hijacked)/COUNT(*), 2)
                 AS blocked_hijacked_average,
             TRUNC(SUM(not_blocked_hijacked)/COUNT(*), 2)
                 AS not_blocked_hijacked_average,
             TRUNC(SUM(blocked_not_hijacked)/COUNT(*), 2)
                 AS blocked_not_hijacked_average,
             TRUNC(SUM(not_blocked_not_hijacked)/COUNT(*), 2)
                 AS not_blocked_not_hijacked_average,
             TRUNC(SUM(percent_blocked_hijacked_out_of_total_hijacks)/COUNT(*)
                 , 2)
                 AS percent_blocked_hijacked_out_of_total_hijacks_average,
             TRUNC(SUM(percent_not_blocked_hijacked_out_of_total_hijacks)
                   /COUNT(*), 2)
                 AS percent_not_blocked_hijacked_out_of_total_hijacks_average,
             TRUNC(SUM(percent_blocked_not_hijacked_out_of_total_prefix_origin_pairs
                 )/COUNT(*), 2)
                 AS
                 percent_blocked_not_hijacked_out_of_total_prefix_origin_pairs_average
             FROM """
    # Returns average statitistics for each policy
    return {x: averages_app.db.execute(sql + x) for x in get_policies()}
