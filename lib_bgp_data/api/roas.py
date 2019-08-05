import functools
from flask import Flask, jsonify, request, Blueprint
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from copy import deepcopy
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils
from .api_utils import format_json
from pprint import pprint

roas_app = Blueprint("roas_app", __name__)

@roas_app.route("/roas_data/")
@format_json(lambda: {"description": "All ROAs used"})
def roas():
    return roas_app.db.execute("SELECT * FROM roas;")
