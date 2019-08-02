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

class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join([BaseConverter.to_url(value)
                        for value in values])



application = Flask(__name__)
swagger = Swagger(application)
application.wsgi_app = ProxyFix(application.wsgi_app)
application.url_map.converters['list'] = ListConverter

@application.before_first_request
def activate_db():
    application.db = Database(Logger({}))

def format_json(metadata_getter):
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(*args, **kwargs):
            start = utils.now()
            # Inside the decorator
            results = func(*args, **kwargs)
            final = {"data": results, "metadata": metadata_getter()}
            api_url = "https://bgpforecast.uconn.edu/"
            data["metadata"]["query_url"] = api_url + request.path
            data["metadata"]["seconds"] = (utils.now() - start).total_seconds()
            return jsonify(dictify(final))
        return function_that_runs_func
    return my_decorator


@application.route("/roas_data/")
@format_json()
def roas():
    return application.db.execute("SELECT * FROM roas;")

@application.route("/relationships_data/<list:asns>")
@format_json()
    results = {}
    if len(asns) == 0:
        return {"peer_data": 
    info = {x: application.db.execute(sql, [x]) for x in validate_asns(asns)}


def get_extrapolator_metadata():
    extrapolator_description = ("All prefix origin pairs within the"
                                " local RIB(s) according to the"
                                " extrapolator-engine")
    return {"description": extrapolator_description}

@swag_from('flasgger_docs/extrapolation.yml')
@application.route("/extrapolator_data/<list:asns>/")
@format_json(get_extrapolator_metadata)
def extrapolation(asns):
    sql = """SELECT DISTINCT mrt.prefix, mrt.origin FROM mrt_w_roas mrt
          LEFT OUTER JOIN
              (SELECT prefix, origin
                  FROM extrapolation_inverse_results
              WHERE asn=%s) exr
          ON mrt.prefix = exr.prefix AND mrt.origin = exr.origin
          WHERE exr.prefix IS NULL OR exr.origin IS NULL;"""
    return {x: application.db.execute(sql, [x]) for x in validate_asns(asns)}

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
 
valid_policies = {"invalid_asn","invalid_length", "rov"}
input_policies = valid_policies.union({"all"})

def validate_asns(asns):
    try:
        return [int(asn) for asn in deepcopy(asns)]
    except ValueError:
        return []


def policy_stats_validation(asns, policies):
    if "all" in policies:
        policies = valid_policies
    for policy in policies:
        if policy not in input_policies:
            return [], []
    asns = validate_asns(asns)
    return asns, policies

def convert_stubs_to_parent_asn(asn):
    results = application.db.execute("SELECT * FROM stubs WHERE stub_asn=%s", [asn])
    if len(results) == 0:
        return asn
    else:
        return results[0]["parent_asn"]

def compute_extra_stats(results):
    for policy in results:
        for asn in dictify(results[policy]):
            current = results[policy][asn]
            total_hijacks = current["blocked_hijacked"]\
                + current["not_blocked_hijacked"]
            current["percent_blocked_hijacked_out_of_total_hijacks"] =\
                current["blocked_hijacked"]*100//total_hijacks
            current["percent_not_blocked_hijacked_out_of_total_hijacks"] =\
                current["not_blocked_hijacked"]*100//total_hijacks
            current["percent_blocked_not_hijacked_out_of_total_prefix_origin_pairs"] =\
                current["blocked_not_hijacked"]*100//\
                current["not_blocked_not_hijacked"]
        num_asns = len(results[policy])
        results[policy]["average"] = {}
        current = results[policy]["average"]
        for key in results[policy][asn]:
            if key == "parent_asn" or "info" in key:
                continue
            results[policy]["average"][key] = 0
            for asn in dictify(results[policy]):
                if asn == "average":
                    continue
                results[policy]["average"][key] += results[policy][asn][key]
            results[policy]["average"][key] /= num_asns

def get_stats(asn, policy, hijack_info=True):
    asn = convert_stubs_to_parent_asn(asn)
    results = application.db.execute("SELECT * FROM {} WHERE parent_asn={}".format(policy, asn))
    if len(results) == 0:
        results = [{}]
    else:
        if hijack_info:
            get_hijack_data(asn, policy, results[0])

    return results[0]    

def dictify(result):
    if not isinstance(result, dict):
        return result
    formatted = {key: dictify(val) for key, val in result.items()}
    if "url" in formatted:
        formatted["url"] = "https://bgpstream.com{}".format(formatted["url"])
    return formatted

def get_hijack_data(asn, policy, info):
    db = application.db
    og_sql = """SELECT DISTINCT ph.prefix, ph.origin, ph.url
             FROM (
                 SELECT ta.asn, iabh.prefix, iabh.origin, iabh.url
                     FROM total_announcements ta
                 CROSS JOIN
                     input iabh
                 WHERE ta.asn = {}) ph
             LEFT JOIN extrapolation_inverse_results exr
                 ON exr.asn = ph.asn
                     AND exr.prefix = ph.prefix
                     AND exr.origin = ph.origin
             WHERE exr.prefix IS NULL""".format(asn)

    if policy == "rov":
        policies = ["invalid_asn", "invalid_length"]
    else:
        policies = [policy]

    for policy in policies:
        info[policy + "_info"] = {}
        for i in ["blocked_hijacked", "not_blocked_hijacked"]:
            sql = og_sql.replace("input", "{}_{}".format(policy, i))
            descriptor = "{}_info".format(i)
            info[policy + "_info"][descriptor] = [dictify(x) for x in db.execute(sql)]
       

@application.route("/policy_stats/with_hijacks/<list:asns>/<list:policies>/")
@format_json(get_policy_metadata)
def policy_stats_with_hijacks(asns, policies):
    return policy_stats(asns, policies, hijack_info=True)


@application.route("/policy_stats/without_hijacks/<list:asns>/<list:policies>/")
@format_json(get_policy_metadata)
def policy_stats_without_hijacks(asns, policies):
    return policy_stats(asns, policies, hijack_info=False)


def policy_stats(asns, policies, hijack_info):
    start = utils.now()
    # Should move this out of here, should only be initialized once, but
    # must be done with some kind of func call, cannot be global or else
    # screws up installation script
    asns, policies = policy_stats_validation(asns, policies)
    if len(asns) == 0 or len(policies) == 0:
        return jsonify({})
    results = {}
    for policy in policies:
        results[policy] = {}
        for asn in asns:
            results[policy][str(asn)] = dictify(get_stats(asn,
                                                     policy,
                                                     hijack_info))
    compute_extra_stats(results)   
    return results
