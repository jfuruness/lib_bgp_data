from flask import Flask, jsonify
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils, Stubs_Table


class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join([BaseConverter.to_url(value)
                        for value in values])


# TODO: Delete this functions once we implement ability of getting history data from database
def rand_num_array(length):
    """
    Create an array of random numbers of the given length
    """

    return [int(random() * 100) for i in range(length)]


# TODO: Delete this functions once we implement ability of getting history data from database
def stat_history_producer(length):
    """
    Produces fake history data for all the policies, for a given amount of days (i.e. length)
    """
    asn_stats_history = {
        'simpleTimeHeuristic': {
            'neitherBlockedNorHijacked': rand_num_array(length),
            'hijackedAndBlocked': rand_num_array(length),
            'notHijackedButBlocked': rand_num_array(length),
            'hijackedButNotBlocked': rand_num_array(length)
        },
        'rov': {
            'neitherBlockedNorHijacked': rand_num_array(length),
            'hijackedAndBlocked': rand_num_array(length),
            'notHijackedButBlocked': rand_num_array(length),
            'hijackedButNotBlocked': rand_num_array(length)
        },
        'deprefer': {
          'neitherBlockedNorHijacked': rand_num_array(length),
          'hijackedAndBlocked': rand_num_array(length),
          'notHijackedButBlocked': rand_num_array(length),
          'hijackedButNotBlocked': rand_num_array(length)
        }
    }

    # Create timestamps
    dates = []
    today = datetime.today()
    for i in range(length, 0, -1):
        date = today - timedelta(days=i)
        # dates.append(date.strftime('%Y-%m-%d'))
        dates.append(date.isoformat())

    result = {
        'timestamps': dates,
        'history': asn_stats_history
    }

    return result


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

def form_sql(table_name, asns):
    sql = "SELECT * FROM "
    sql += table_name
    sql += " WHERE asn={}".format(asns[0])
    if len(asns) > 1:
        for asn in asns[0:]:
            sql += " OR asn=%s "
    sql += ";"
    return sql


    

@swag_from('flasgger_docs/asn_hijack_stats.yml')
@application.route("/asn_policy_stats/<list:asns>/<list:policies>/")
def asn_policy_stats(asns, policies):
    # Should move this out of here, should only be initialized once, but
    # must be done with some kind of func call, cannot be global or else
    # screws up installation script
    db = Database(Logger({}))

    sqls = []
    if "all" in policies:
        policies = ["invalid_asn"]#, "invalid_length", "rov", "time_heuristic"]
    if "invalid_asn" in policies:
       sqls.append(form_sql("invalid_asn_policy", asns))
       print(sqls)
#    if "invalid_length" in policies:
#        sqls.append(form_sql("invalid_length_policy", asns))
#    if "rov" in policies:
#        sqls.append(form_sql("rov_policy", asns))
#    if "time_heuristic" in policies:
#        sqls.append(form_sql("time_heuristic_policy", asns))
    for sql in sqls:
        db.cursor.execute(sql)
        results = db.cursor.fetchall()
        result = results[0]
        for result in results:
            print([(key, val) for key, val in result.items()])
    stats = {asns[0]:
                {'parent_if_stub_as': '',
                 'Enforce Invalid ASN Only':
                    {'neitherBlockedNorHijacked': result["not_hijacked_not_blocked"],
                     'hijackedAndBlocked': result["hijack_blocked"],
                     'notHijackedButBlocked': result["not_hijacked_blocked"],
                     'hijackedButNotBlocked': result["hijack_not_blocked"],#result["hijacked_not_blocked"],
                     'description': 'Block route announcements using standard Resources Certification (RPKI) Route Origin Validation (ROV)'
                      },
                'ROV':
                    {'neitherBlockedNorHijacked': 5,
                     'hijackedAndBlocked': 6,
                     'notHijackedButBlocked': 7,
                     'hijackedButNotBlocked': 8,
                     'description': 'Block route announcements using standard Resources Certification (RPKI) Route Origin Validation (ROV)'
                      },
                'Simple Time Heuristic':
                    {'neitherBlockedNorHijacked': 9,
                     'hijackedAndBlocked': 10,
                     'notHijackedButBlocked': 11,
                     'hijackedButNotBlocked': 12,
                     'description': 'Block route announcements using standard Resources Certification (RPKI) Route Origin Validation (ROV) and certain time parameters'
                     },
                'Enforce Invalid Length Only':
                    {'neitherBlockedNorHijacked': 13,
                     'hijackedAndBlocked': 14,
                     'notHijackedButBlocked': 15,
                     'hijackedButNotBlocked': 16,
                     'description': 'Block route announcements using standard Resources Certification (RPKI) Route Origin Validation (ROV) if invalid_length'
                     },
                'Pass If No Alternative Route':
                    {'neitherBlockedNorHijacked': 0,
                     'hijackedAndBlocked': 0,
                     'notHijackedButBlocked': 0,
                     'hijackedButNotBlocked': 0,
                     'description': 'incomplete'
                     }
                }}
    return jsonify(stats)


@swag_from('flasgger_docs/asn_history.yml')
@application.route('/asn_history/<asn>/<policy>/<length>/')
def asn_history(asn, policy, length):
    result = {}
    history_data = stat_history_producer(int(length))

    if policy == 'all':
        result[asn] = history_data
    else:
        result[asn] = {
            'timestamps': history_data['timestamps'],
            'history': {
                policy: history_data['history'][policy]
            }
        }

    return jsonify(result)

if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
