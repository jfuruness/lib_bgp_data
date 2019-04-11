# Flask stuff
from flask import Flask, jsonify, send_file
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
# Utility modules
from random import random
from datetime import datetime, timedelta
# API Docs
from flasgger import Swagger, swag_from


####################################################################
# Constants
####################################################################

# List of policies we offer
policies = ['simpleTimeHeuristic', 'rov', 'deprefer']

# This is a fake source of AS stats (only for making the API usuable for frontend testing)
# TODO: Delete this variable after we implement ability of getting data from database
asn_stats = {
  'simpleTimeHeuristic': {
      'neitherBlockedNorHijacked': int(random() * 100),
      'hijackedAndBlocked': int(random() * 100),
      'notHijackedButBlocked': int(random() * 100),
      'hijackedButNotBlocked': int(random() * 100)
  },
  'rov': {
      'neitherBlockedNorHijacked': int(random() * 100),
      'hijackedAndBlocked': int(random() * 100),
      'notHijackedButBlocked': int(random() * 100),
      'hijackedButNotBlocked': int(random() * 100)
  },
  'deprefer': {
    'neitherBlockedNorHijacked': int(random() * 100),
    'hijackedAndBlocked': int(random() * 100),
    'notHijackedButBlocked': int(random() * 100),
    'hijackedButNotBlocked': int(random() * 100)
  }
}

# Holds descriptions of all the policies
policy_descriptions = {
    'simpleTimeHeuristic': {
        'fullName': 'Simple-Time-Based-Heuristic',
        'short_desc': 'Determines legitimacy based on how long an announcement has been around',
        'long_desc': 'Route Hijacks tend to be short lived, so long-standing announcements with an invalid ROA are more likely to be valid routes with improperly configured RPKI than actual attacks. This policy will, for example, output “Whitelist” if a year-old announcement has an invalid ROA and the parameter for “Whitelist” is 10 months.'
    },
    'rov': {
        'fullName': 'Enforce-Invalid_ASN-Only',
        'short_desc': 'Drops annoucements that do not have valid ROAs',
        'long_desc': 'This policy examines the type of invalidity which will be either “INVALID_ASN” or “INVALID_LENGTH”. INVALID_ASN means that the AS announcing the prefix is not the one specified in the ROA. INVALID_LENGTH, means that, although the correct AS is announcing the prefix, the length is outside the range specified in the ROA.'
    },
    'deprefer': {
        'fullName': 'Enforce-If-No-Alternative Announcement',
        'short_desc': 'If the best route is not available, picks second best route if there is one',
        'long_desc': 'If an announcement is invalid according to RPKI and no alternative routes to the origin exist, then it should be dropped. This policy outputs'
    },
}


####################################################################
# Auxiliary Classes and Functions
####################################################################

#-------------------------------------------------------
# Classes
#-------------------------------------------------------

# TODO: Do we need this class?
class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(BaseConverter.to_url(value)
                        for value in values)


#-------------------------------------------------------
# Functions
#-------------------------------------------------------

# TODO: Delete this functions once we implement ability of getting history data from database
def rand_num_array(length):
    """
    Create an array of random numbers of the given length
    """
    result = []
    for i in range(length):
        result.append(int(random() * 100))
    return result


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


####################################################################
# Flask App Settings
####################################################################

app = Flask(__name__, static_url_path='/extrapolation_results')
app.wsgi_app = ProxyFix(app.wsgi_app)
app.url_map.converters['list'] = ListConverter
swagger = Swagger(app)


####################################################################
# API Endpoints
####################################################################

@app.route('/asn_hijack_stats/<asn>/<policy>/')
@swag_from('flasgger_docs/asn_hijack_stats.yml')
def asn_hijack_stats(asn, policy):
    result = {}

    if policy == 'all':
        for ply in policies:
            result[asn] = {
                'fullName':  policy_descriptions[ply]['fullName'],
                'desc': policy_descriptions[ply]['short_desc'],
                'stats': asn_stats
            }
    else:
        result[asn] = {
            'fullName':  policy_descriptions[policy]['fullName'],
            'desc': policy_descriptions[policy]['short_desc'],
            'stats': asn_stats[policy]
        }

    return jsonify(result)


@app.route('/extrapolation/<asn>/')
@swag_from('flasgger_docs/extrapolation.yml')
def extrapolation(asn):
    return send_file('extrapolation_results/extrapolation_results.csv', as_attachment=True)


@app.route('/policy_descriptions/<policy>/')
@swag_from('flasgger_docs/policy_descriptions.yml')
def policy_description_route(policy):
    result = {}

    if policy == 'all':
        for ply in policies:
            result[ply] = policy_descriptions[ply]
    else:
        result[policy] = policy_descriptions[policy]

    return jsonify(result)


@app.route('/asn_history/<asn>/<policy>/<length>/')
@swag_from('flasgger_docs/asn_history.yml')
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


####################################################################
# For Development Testing Only
####################################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
