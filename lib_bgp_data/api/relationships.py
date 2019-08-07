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
from .api_utils import validate_asns, format_json
from ..rpki_validator import RPKI_Validator
from pprint import pprint

relationships_app = Blueprint("relationships_app", __name__)

@relationships_app.route("/relationships/<list:asns>")
@swag_from("flasgger_docs/relationships.yml")
@format_json(lambda: {"description": "Relationship data according to Caida."})
def relationships(asns):
    data = {}
    for asn in validate_asns(asns, relationships_app.db):
        data[asn] = {"peers": _get_peers(asn)}
        data[asn]["customers"] = _get_customers(asn)
        data[asn]["providers"] = _get_providers(asn)
    #data["all_data"] = _get_relationship_data() omitted due to time it takes
    return data

def _get_peers(asn):
    peers = []
    sql = "SELECT * FROM peers WHERE peer_as_1=%s OR peer_as_2 = %s;"
    results = relationships_app.db.execute(sql, [asn, asn])
    if len(results) > 0:
        for result in results:   
            for key, val in result.items():
                if val != asn:
                    peers.append(val)
    return peers

def _get_customers(asn):
    sql = "SELECT * FROM customer_providers WHERE provider_as=%s"
    results = relationships_app.db.execute(sql, [asn])
    if len(results) > 0:
        return [x["customer_as"] for x in results]
    else:
        return []

def _get_providers(asn):
    sql = "SELECT * FROM customer_providers WHERE customer_as=%s"
    results = relationships_app.db.execute(sql, [asn])
    if len(results) > 0:
        return [x["provider_as"] for x in results]
    else:
        return []

def _get_relationship_data():
    sqls = {"peers": "SELECT * FROM peers;",
            "provider_customers": "SELECT * FROM customer_providers;"}
    return {k: relationships_app.db.execute(sql) for k, sql in sqls.items()}
