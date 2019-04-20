from flask import Flask, jsonify
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter


class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(BaseConverter.to_url(value)
                        for value in values)


application = Flask(__name__)
application.wsgi_app = ProxyFix(application.wsgi_app)
application.url_map.converters['list'] = ListConverter

@application.route("/<list:asns>/<list:policies>/")
def forecast_api(asns, policies):
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

if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
