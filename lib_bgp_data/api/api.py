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

valid_policies = {"invalid_asn_policy","invalid_length_policy", "rov_policy"}
input_policies = valid_policies.union({"all"})
    

def policy_stats_validation(asns, policies):
    if "all" in policies:
        policies = valid_policies
    for policy in policies:
        if policy not in input_policies:
            return []
    try:
        asns = [int(asn) for asn in deepcopy(asns)]
    except ValueError:
        return []
    return asns, policies

def get_policy_stats_result(asn, policy, db):
    results = db.execute("SELECT * FROM {} WHERE parent_asn={}".format(policy, asn))
    if len(results) == 0:
        sql = """SELECT * FROM {0} INNER JOIN stubs ON {0}.parent_asn=stubs.parent_asn
              WHERE stubs.stub_asn = {1}""".format(policy, asn)
        results = db.execute(sql)
        if len(results) == 0:
            results = [{}]
        results[0].pop("stub_asn")
    return results[0]    

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
            result = get_policy_stats_result(asn, policy, db)
            results[policy][asn] = {key: val for key, val in result.items()}
    return jsonify(results)

if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
