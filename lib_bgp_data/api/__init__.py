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
    application.run(debug=True)
