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

hijacks_app = Blueprint("hijacks_app", __name__)

def get_hijack_metadata(blocked_or_not=None, policy=None):
    conds_list = ["Covered by a ROA",
                  ["The time of the hijack overlaps with the sample time",
                   ("Note that if there is no end time on"
                    " https://bgpstream.comthe hijack is considered ongoing")],
                  "The hijack can be found in our MRT announcements data"]

    if None not in [blocked_or_not, policy]:
        conds_list.append("{} by {}".format(blocked_or_not, policy))

    return {"description": {"All bgpstream.com hijacks that are:": conds_list}}

@hijacks_app.route("/invalid_asn_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_asn_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "blocked", "invalid_asn")
def invalid_asn_blocked_hijacked():
    sql = "SELECT * FROM invalid_asn_blocked_hijacked;"
    return hijacks_app.db.execute(sql)

@hijacks_app.route("/invalid_asn_not_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_asn_not_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "not blocked", "invalid_asn")
def invalid_asn_not_blocked_hijacked():
    sql = "SELECT * FROM invalid_asn_not_blocked_hijacked;"
    return hijacks_app.db.execute(sql)

@hijacks_app.route("/invalid_length_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_length_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "not blocked", "invalid_length")
def invalid_length_blocked_hijacked():
    sql = "SELECT * FROM invalid_length_blocked_hijacked;"
    return hijacks_app.db.execute(sql)

@hijacks_app.route("/invalid_length_not_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_length_not_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "not blocked", "invalid_length")
def invalid_length_not_blocked_hijacked():
    sql = "SELECT * FROM invalid_length_not_blocked_hijacked;"
    return hijacks_app.db.execute(sql)

@hijacks_app.route("/hijack_data/")
@swag_from("flasgger_docs/hijacks.yml")
@format_json(get_hijack_metadata)
def hijack():
    sqls = ["SELECT * FROM invalid_asn_blocked_hijacked;",
            "SELECT * FROM invalid_asn_not_blocked_hijacked;"]
    results = []
    for sql in sqls:
        results.extend(hijacks_app.db.execute(sql))
    return results
