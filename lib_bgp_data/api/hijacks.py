import functools
from flask import Flask, jsonify, request
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from copy import deepcopy
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils
from pprint import pprint

@application.route("/invalid_asn_blocked_hijacked_data/")
@format_json(get_hijack_metadata, "blocked", "invalid_asn")
def invalid_asn_blocked_hijacked():
    sql = "SELECT * FROM invalid_asn_blocked_hijacked;"
    return application.db.execute(sql)

@application.route("/invalid_asn_not_blocked_hijacked_data/")
@format_json(get_hijack_metadata, "not blocked", "invalid_asn")
def invalid_asn_not_blocked_hijacked():
    sql = "SELECT * FROM invalid_asn_not_blocked_hijacked;"
    return application.db.execute(sql)

@application.route("/invalid_length_blocked_hijacked_data/")
@format_json(get_hijack_metadata, "not blocked", "invalid_asn")
def invalid_length_blocked_hijacked():
    sql = "SELECT * FROM invalid_length_blocked_hijacked;"
    return application.db.execute(sql)

@application.route("/invalid_length_not_blocked_hijacked_data/")
@format_json(get_hijack_metadata, "not blocked", "invalid_asn")
def invalid_length_not_blocked_hijacked():
    sql = "SELECT * FROM invalid_length_not_blocked_hijacked;"
    return application.db.execute(sql)

@application.route("/hijack_data/")
@format_json(get_hijack_metadata)
def hijack():
    sqls = ["SELECT * FROM invalid_asn_blocked_hijacked;",
            "SELECT * FROM invalid_asn_not_blocked_hijacked;"]
    return [*application.db.execute(sql) for sql in sqls]

def get_hijack_metadata(blocked_or_not=None, policy=None):
    conds_list = ["Covered by a ROA",
                  ["The time of the hijack overlaps with the sample time",
                   ("Note that if there is no end time on"
                    " https://bgpstream.comthe hijack is considered ongoing")],
                  "The hijack can be found in our MRT announcements data"]

    if None not in [blocked_or_not, policy]:
        conds_list.append( "{} by {}".format(blocked_or_not, policy)

    descr = {"description": {("All hijacks from bgpstream.com that meet"
                              " these conditions:)": conds_dict}}
