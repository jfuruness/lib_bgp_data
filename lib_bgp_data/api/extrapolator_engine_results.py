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

extrapolator_engine_results_app = Blueprint("extrapolator_engine_results_app",
                                            __name__)

def get_extrapolator_metadata():
    extrapolator_description = ("All prefix origin pairs within the"
                                " local RIB(s) according to the"
                                " extrapolator-engine")
    return {"description": extrapolator_description}

@extrapolator_engine_results_app.route("/extrapolator_data/<list:asns>/")
@format_json(get_extrapolator_metadata)
def extrapolation(asns):
    db = extrapolator_engine_results_app.db
    sql = """SELECT DISTINCT mrt.prefix, mrt.origin FROM mrt_w_roas mrt
          LEFT OUTER JOIN
              (SELECT prefix, origin
                  FROM extrapolation_inverse_results
              WHERE asn=%s) exr
          ON mrt.prefix = exr.prefix AND mrt.origin = exr.origin
          WHERE exr.prefix IS NULL OR exr.origin IS NULL;"""
    return {x: db.execute(sql, [x]) for x in validate_asns(asns, db)}
