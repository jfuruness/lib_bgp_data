import functools
from flask import Flask, jsonify, request
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import BaseConverter
from random import random
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
from copy import deepcopy
from decimal import Decimal
from ..utils import Database, db_connection, Thread_Safe_Logger as Logger
from ..utils import utils
from pprint import pprint

class InvalidInput(Exception):
    pass

def format_json(metadata_getter, *args1):
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(*args2, **kwargs):
            try:
                start = utils.now()
                # Inside the decorator
                results = func(*args2, **kwargs)
                final = {"data": results, "metadata": metadata_getter(*args1)}
                api_url = "https://bgpforecast.uconn.edu"
                meta = final["metadata"]
                meta["query_url"] = api_url + request.path
                meta["seconds"] = (utils.now() - start).total_seconds()
                return jsonify(dictify(final))
            except InvalidInput:
                return jsonify({"ERROR": "Invalid input"})
            except Exception as e:
                print(e)
                return jsonify({"ERROR": "Please contact jfuruness@gmail.com"})
                
        return function_that_runs_func
    return my_decorator

def validate_asns(asns, db):
    try:
        asns = [int(asn) for asn in deepcopy(asns)]
        return convert_stubs_to_parents(asns, db)
    except ValueError:
        raise InvalidInput

def validate_policies(policies):
    valid_policies = {"invalid_asn","invalid_length", "rov"}
    if "all" in policies:
        policies = valid_policies
    for policy in policies:
        if policy not in valid_policies.union({"all"}):
            raise InvalidInput
    return policies

def convert_stubs_to_parents(asns, db):
    list_of_asns = []
    sql = "SELECT * FROM stubs WHERE stub_asn=%s"
    for asn in asns:
        results = db.execute(sql, [asn])
        if len(results) == 0:
            list_of_asns.append(asn)
        else:
            list_of_asns.append(results[0]["parent_asn"])
    return list_of_asns

def dictify(result):
    if not isinstance(result, dict):
        if isinstance(result, list):
            return [dictify(x) for x in result]
        if isinstance(result, Decimal):
            return float(result)
        return result
    formatted = {key: dictify(val) for key, val in result.items()}
    if "url" in formatted:
        formatted["url"] = "https://bgpstream.com{}".format(formatted["url"])
    return formatted
