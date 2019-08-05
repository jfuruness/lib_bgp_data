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
from .api_utils import validate_asns, validate_policies, format_json
from pprint import pprint

@application.route("/policy_stats/<list:asns>/<list:policies>/")
@format_json(get_policy_metadata)
def policy_stats(asns, policies):
    asns, policies = validate_asns_and_policies(asns, policies)
    results = {policy: {} for policy in policies}
    for policy in policies:
        for asn in asns:
            results[policy][str(asn)] = get_stats(asn, policy)
            results[policy][str(asn)].update(get_hijack_data(asn, policy))
        results.update(get_average_stats(dictify(results[policy])))
    return results

def get_stats(asn, policy):
    sql = "SELECT * FROM {} WHERE parent_asn={}".format(policy, asn)
    results = application.db.execute(sql)
    if len(results) == 0:
        results = [{}]
    return results[0]

def get_average_stats(policy_dict):
    num_asns = len(policy_dict)
    average = {}
    for key in policy_dict[asn]:
        if key == "parent_asn" or "hijack_data" in key:
            continue
        average[key] = sum([policy_dict[x][key] for x in policy_dict])/num_asns
    return average

def get_hijack_data(asn, pol):
    info = {}
    og_sql = """SELECT iabh.prefix, iabh.origin, iabh.url 
             FROM input iabh
               LEFT OUTER JOIN 
                 (SELECT * FROM extrapolation_inverse_results
                     WHERE asn={}) exr
             ON exr.prefix = iabh.prefix AND exr.origin = iabh.origin
             WHERE exr.prefix IS NULL AND exr.origin IS NULL;""".format(asn)

    policies = ["invalid_asn", "invalid_length"] if pol == "rov" else [pol]

    for policy in policies:
        p_descr = "{}_hijack_data".format(policy)
        info[p_descr] = {}
        for y in ["blocked_hijacked", "not_blocked_hijacked"]:
            sql = og_sql.replace("input", "{}_{}".format(policy, y))
            info[p_descr]["{}_info".format(y)] = [x for x in
                                                  application.db.execute(sql)]
    return info

def get_policy_descriptions():
    return {"rov": ("Block route announcements using standard"
                    " Resource Certification (RPKI) Route Origin"
                    " Validation (ROV) as defined in RFC 6811"),
            "invalid_asn": ("Block route announcements only when"
                            " the originating AS is in conflict"
                            " with a Route Origin Authorization"
                            " (ROA). Announcements containing"
                            " prefixes exceeding the maximum length"
                            " authorized by a ROA are allowed."),
            "invalid_length": ("Block route announcements only"
                               " when the length of the announced"
                               " prefix exceeds the maximum length"
                               " authorized by a ROA."
                               " Announcements originating from an"
                               " AS that is not authorized to do"
                               " so are allowed.")}
def get_policy_metadata():
    metadata = {"disclaimers": ("All announcements and hijacks in this"
                               " dataset are covered by a ROA. In other"
                               " words, the prefixes are a subset of a"
                               " ROA.")}
    metadata.update(get_policy_descriptions())
    return metadata
