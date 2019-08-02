import functools
from flask import Flask, jsonify, request
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from copy import deepcopy
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils
from pprint import pprint

def get_extrapolator_metadata():
    extrapolator_description = ("All prefix origin pairs within the"
                                " local RIB(s) according to the"
                                " extrapolator-engine")
    return {"description": extrapolator_description}

@swag_from('flasgger_docs/extrapolation.yml')
@application.route("/extrapolator_data/<list:asns>/")
@format_json(get_extrapolator_metadata)
def extrapolation(asns):
    sql = """SELECT DISTINCT mrt.prefix, mrt.origin FROM mrt_w_roas mrt
          LEFT OUTER JOIN
              (SELECT prefix, origin
                  FROM extrapolation_inverse_results
              WHERE asn=%s) exr
          ON mrt.prefix = exr.prefix AND mrt.origin = exr.origin
          WHERE exr.prefix IS NULL OR exr.origin IS NULL;"""
    return {x: application.db.execute(sql, [x]) for x in validate_asns(asns)}
