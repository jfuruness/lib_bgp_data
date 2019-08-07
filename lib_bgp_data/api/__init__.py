#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the create_app function to run the API.

This API includes endpoints to get:
    -Every variation of hijack data
    -ROAs data
    -Relationship data for specific asns
    -Extrapolator data for specific asns
    -Policy statistics for specific asns and policies
        -Including aggregate averages for ASNs
    -Average policy statistics
    -RPKI validity results

Design Choices:
    -Extrapolator data is not done in advance because the size of the
     table is too large
    -flasgger docs are in separate files for readability
    -All relationship data was not returned due to time constraints
    -Separate blueprints are used for code readability

Possible Future Improvements:
    -Convert all stubs to parent ASNs at once
    -Have better logging - record to files and alerts when errors occur
"""

from flask import Flask
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from flasgger import Swagger
from ..utils import Database, Thread_Safe_Logger as Logger

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Reynaldo Morillo"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# http://exploreflask.com/en/latest/views.html#custom-converters
class ListConverter(BaseConverter):
    """Converts a comma separated url into a list."""

    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join([BaseConverter.to_url(value)
                        for value in values])

def create_app(args={}):
    """Creates the application and runs it."""

    application = Flask(__name__)
    # For flasgger docs
    swagger = Swagger(application)
    # Fixes the proxy problems we've been having
    application.wsgi_app = ProxyFix(application.wsgi_app)
    # For the list converter
    application.url_map.converters['list'] = ListConverter
    # Creates the database
    application.db = Database(Logger(args))

    # Imports all the blueprints that we have
    # From the flask tutorial I watched they did it all here,
    # so I assume that is correct
    from .averages import averages_app
    from .extrapolator_engine_results import extrapolator_engine_results_app\
        as exr_app
    from .hijacks import hijacks_app
    from .policies import policies_app
    from .relationships import relationships_app
    from .roas import roas_app
    from .rpki_validity_results import RPKI_app
    

    for sub_app in [averages_app, exr_app, hijacks_app, policies_app,
                    relationships_app, roas_app, RPKI_app]:
        # Sets the database
        sub_app.db = application.db
        # Registers the blueprint
        application.register_blueprint(sub_app)

    # Runs the application. Do NOT use in prod!!!
    application.run(host='0.0.0.0', debug=True)
