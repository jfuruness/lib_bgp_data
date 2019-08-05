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
from ..rpki_validator import RPKI_Validator
from .api_utils import format_json
from pprint import pprint

RPKI_app = Blueprint("RPKI_app", __name__)

def get_rpki_validator_metadata():
    return {"description": "Validity data from the RPKI validator.",
            "decoder": RPKI_Validator.get_validity_dict()}

@RPKI_app.route("/rpki_validator_data/")
@format_json(get_rpki_validator_metadata)
def rpki_validator_data():
    return RPKI_app.db.execute("SELECT * FROM rov_validity;")
