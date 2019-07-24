from flask import Flask, jsonify
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from copy import deepcopy
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils


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
#db = Database(Logger({}))

@swag_from('flasgger_docs/extrapolation.yml')
@application.route("/extrapolator/inverse/<list:asns>/")
def extrapolation(asns):
	extrapolator_results = {"012": {"prefix": 123,
					"origin": 345
					},
				"description": "All prefixes that where not seen at that asn"
				}
	return jsonify(extrapolator_results)

valid_policies = {"invalid_asn","invalid_length", "rov"}
input_policies = valid_policies.union({"all"})
    
descriptions = {"rov": ("Block route announcements using standard"
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
disclaimers = {"disclaimers": ("All announcements and hijacks in this"
                               " dataset are covered by a roa. In other"
                               " words, the prefixes are a subset of a"
                               "roa.")}


def policy_stats_validation(asns, policies):
    if "all" in policies:
        policies = valid_policies
    for policy in policies:
        if policy not in input_policies:
            return [], []
    try:
        asns = [int(asn) for asn in deepcopy(asns)]
    except ValueError:
        return [], []
    return asns, policies

def convert_stubs_to_parent_asn(asn, db):
    results = db.execute("SELECT * FROM stubs WHERE stub_asn=%s", [asn])
    if len(results) == 0:
        return asn
    else:
        return results[0]["parent_asn"]

def get_stats(asn, policy, db):
    asn = convert_stubs_to_parent_asn(asn, db)
    results = db.execute("SELECT * FROM {} WHERE parent_asn={}".format(policy, asn))
    if len(results) == 0:
        results = [{}]
    else:
        get_hijack_data(asn, policy, results[0], db)

    return results[0]    

def dictify(result):
    formatted = {key: val for key, val in result.items()}
    if "url" in formatted:
        formatted["url"] = "bgpstream.com{}".format(formatted["url"])
    return formatted

def get_hijack_data(asn, policy, info, db):
    og_sql = """SELECT ph.prefix, ph.origin, ph.url
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
        info[policy] = {}
        for i in ["blocked_hijacked", "not_blocked_hijacked"]:
            sql = og_sql.replace("input", "{}_{}".format(policy, i))
            descriptor = "{}_{}_info".format(policy, i)
            print("!!!!")
            print(sql)
            info[policy][descriptor] = [dictify(x) for x in db.execute(sql)]
       

@swag_from('flasgger_docs/asn_hijack_stats.yml')
@application.route("/asn_policy_stats/<list:asns>/<list:policies>/")
def asn_policy_stats(asns, policies):
    # Should move this out of here, should only be initialized once, but
    # must be done with some kind of func call, cannot be global or else
    # screws up installation script
    db = Database(Logger({}))
    asns, policies = policy_stats_validation(asns, policies)
    results = {}
    for policy in policies:
        results[policy] = {}
        for asn in asns:
            results[policy][asn] = dictify(get_stats(asn, policy, db))
    final = {}
    final["data"] = results
    final["metadata"] = {key: val for key, val in descriptions.items()
                           if key in policies}
    final["metadata"].update(disclaimers)
    return jsonify(final)
