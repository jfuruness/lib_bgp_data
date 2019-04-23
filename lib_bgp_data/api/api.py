from flask import Flask, jsonify
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from


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


@swag_from('flasgger_docs/extrapolation.yml')
@application.route("/extrapolator/inverse/<list:asns>/")
def extrapolation(asns):
	extrapolator_results = {"012": {"prefix": 123,
					"origin": 345
					},
				"description": "All prefixes that where not seen at that asn"
				}
	return jsonify(extrapolator_results)


@swag_from('flasgger_docs/asn_hijack_stats.yml')
@application.route("/<list:asns>/<list:policies>/")
def asn_hijack_stats(asns, policies):
#    db = Database(Logger({}).logger)
    stats = {"123":
                {'parent_if_stub_as': '1234',
                 'Simple Time Heuristic':
                    {'neitherBlockedNorHijacked': 1,
                     'hijackedAndBlocked': 2,
                     'notHijackedButBlocked': 3,
                     'hijackedButNotBlocked': 4,
                     'description': 'Block route announcements using standard Resources Certification (RPKI) Route Origin Validation (ROV)'
                      },
                'ROV':
                    {'neitherBlockedNorHijacked': 5,
                     'hijackedAndBlocked': 6,
                     'notHijackedButBlocked': 7,
                     'hijackedButNotBlocked': 8,
                     'description': 'Hello Cameron'
                      },
                'Enforce Invalid ASN ONly':
                    {'neitherBlockedNorHijacked': 9,
                     'hijackedAndBlocked': 10,
                     'notHijackedButBlocked': 11,
                     'hijackedButNotBlocked': 12,
                     'description': 'Block route announcements based on certain ROA rules'
                     },
                'Enforce Invalid Length ONly':
                    {'neitherBlockedNorHijacked': 13,
                     'hijackedAndBlocked': 14,
                     'notHijackedButBlocked': 15,
                     'hijackedButNotBlocked': 16,
                     'description': 'help'
                     },
                'Pass If No Alternative Route':
                    {'neitherBlockedNorHijacked': 17,
                     'hijackedAndBlocked': 18,
                     'notHijackedButBlocked': 19,
                     'hijackedButNotBlocked': 20,
                     'description': 'incomplete'
                     }
                },
            "456":
                {'parent_if_stub_as': '',
                 'Simple Time Heuristic':
                    {'neitherBlockedNorHijacked': 1,
                     'hijackedAndBlocked': 2,
                     'notHijackedButBlocked': 3,
                     'hijackedButNotBlocked': 4,
                     'description': 'Block route announcements using standard Resources Certification (RPKI) Route Origin Validation (ROV)'
                      },
                'ROV':
                    {'neitherBlockedNorHijacked': 5,
                     'hijackedAndBlocked': 6,
                     'notHijackedButBlocked': 7,
                     'hijackedButNotBlocked': 8,
                     'description': 'Hello Cameron'
                      },
                'Enforce Invalid ASN Only':
                    {'neitherBlockedNorHijacked': 9,
                     'hijackedAndBlocked': 10,
                     'notHijackedButBlocked': 11,
                     'hijackedButNotBlocked': 12,
                     'description': 'Block route announcements based on certain ROA rules'
                     },
                'Enforce Invalid Length Only':
                    {'neitherBlockedNorHijacked': 13,
                     'hijackedAndBlocked': 14,
                     'notHijackedButBlocked': 15,
                     'hijackedButNotBlocked': 16,
                     'description': ''
                     },
                'Pass If No Alternative Route':
                    {'neitherBlockedNorHijacked': 17,
                     'hijackedAndBlocked': 18,
                     'notHijackedButBlocked': 19,
                     'hijackedButNotBlocked': 20,
                     'description': 'incomplete'
                     }
                }
            }
    if '123' not in asns:
        stats.pop('123')
    if '456' not in asns:
        stats.pop('456')
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
