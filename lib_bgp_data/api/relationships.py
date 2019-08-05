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
from ..api_utils import validate_asns
from ..rpki_validator import RPKI_Validator
from pprint import pprint

@application.route("/relationships/<list:asns>")
@format_json(lambda: {"description": "Relationship data according to Caida."})
def relationships(asns):
    data = {}
    for asn in validate_asns(asns):
        data[str(asn)]["peers"] = _get_peers()
        data[str(asn)]["customers"] = _get_customers()
        data[str(asn)]["providers"] = _get_providers()
    data["all_data"] = _get_relationship_data()
    return data

def _get_peers(asn):
    peers = []
    peer_sql = "SELECT * FROM peers WHERE peer_as_1=%s OR peer_as_2 = %s;"
    for result in application.db.execute(sql, [asn]):
        for key, val in result.items():
            if val != asn:
                peers.append(val)
    return peers

def _get_customers(asn):
    sql = "SELECT * FROM customer_providers WHERE provider_as=%s"
    return [x["customer_as"] for x in application.db.execute(sql, [asn])]

def _get_providers(asn):
    sql = "SELECT * FROM customer_providers WHERE customer_as=%s"
    return [x["provider_as"] for x in application.db.execute(sql, [asn])]

def _get_relationship_data():
    sqls = {"peers": "SELECT * FROM peers;",
            "provider_customers": "SELECT * FROM customer_providers;"}
    return {key, appication.db.execute(sql) for key, sql in sqls}
