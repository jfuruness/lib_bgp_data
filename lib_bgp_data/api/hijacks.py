#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for multiple hijack API endpoints.

The endpoints include every possible variation of hijacks.

Design Choices:
    -A separate blueprint was used for readability
"""

from flask import Blueprint
from flasgger import swag_from
from .api_utils import format_json

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


hijacks_app = Blueprint("hijacks_app", __name__)


def get_hijack_metadata(blocked_or_not=None, policy=None):
    """Gets the hijack metadata used by the format_json decorator."""

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
    """Returns all propogated hijacks blocked by invalid asn."""

    sql = "SELECT * FROM invalid_asn_blocked_hijacked;"
    return hijacks_app.db.execute(sql)


@hijacks_app.route("/invalid_asn_not_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_asn_not_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "not blocked", "invalid_asn")
def invalid_asn_not_blocked_hijacked():
    """Returns all propogated hijacks not blocked by invalid asn."""

    sql = "SELECT * FROM invalid_asn_not_blocked_hijacked;"
    return hijacks_app.db.execute(sql)


@hijacks_app.route("/invalid_length_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_length_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "not blocked", "invalid_length")
def invalid_length_blocked_hijacked():
    """Returns all propogated hijacks blocked by invalid length."""

    sql = "SELECT * FROM invalid_length_blocked_hijacked;"
    return hijacks_app.db.execute(sql)


@hijacks_app.route("/invalid_length_not_blocked_hijacked_data/")
@swag_from("flasgger_docs/invalid_length_not_blocked_hijacked.yml")
@format_json(get_hijack_metadata, "not blocked", "invalid_length")
def invalid_length_not_blocked_hijacked():
    """Returns all propogated hijacks not blocked by invalid asn."""

    sql = "SELECT * FROM invalid_length_not_blocked_hijacked;"
    return hijacks_app.db.execute(sql)


@hijacks_app.route("/hijack_data/")
@swag_from("flasgger_docs/hijacks.yml")
@format_json(get_hijack_metadata)
def hijack():
    """Returns all propogated hijacks."""

    sqls = ["SELECT * FROM invalid_asn_blocked_hijacked;",
            "SELECT * FROM invalid_asn_not_blocked_hijacked;"]
    results = []
    for sql in sqls:
        results.extend(hijacks_app.db.execute(sql))
    return results
