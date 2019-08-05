import functools
from flask import Flask, jsonify, request, Blueprint
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from copy import deepcopy
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils
from .api_utils import format_json
from pprint import pprint

averages_app = Blueprint("averages_app", __name__)

@averages_app.route("/averages/")
@swag_from("flasgger_docs/averages.yml")
@format_json(lambda: {"description": "Average data across all ASes"})
def averages():
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
    tables = ["invalid_asn", "invalid_length", "rov"]
    return {x: averages_app.db.execute(sql + x) for x in tables}
