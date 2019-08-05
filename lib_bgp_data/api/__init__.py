from flask import Flask
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from flasgger import Swagger
from ..utils import Database, Thread_Safe_Logger as Logger

class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join([BaseConverter.to_url(value)
                        for value in values])

def create_app(args={}):
    application = Flask(__name__)
    swagger = Swagger(application)
    application.wsgi_app = ProxyFix(application.wsgi_app)
    application.url_map.converters['list'] = ListConverter
    application.db = Database(Logger(args))

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
        sub_app.db = application.db
        application.register_blueprint(sub_app)

    application.run(host='0.0.0.0', debug=True)
