#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for a relationship API endpoint.

This endpoint returns the peers, customers, and providers of an ASN.

Design Choices:
    -All relationship data was not returned due to time constraints
    -A separate blueprint was used for readability
"""

from flask import Blueprint
from flasgger import swag_from
from .api_utils import validate_asns, format_json

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


relationships_app = Blueprint("relationships_app", __name__)


@relationships_app.route("/relationships/<list:asns>")
@swag_from("flasgger_docs/relationships.yml")
@format_json(lambda: {"description": "Relationship data according to Caida."})
def relationships(asns):
    """Returns relationship data for a specific asn."""

    data = {}
    for asn in validate_asns(asns, relationships_app.db):
        data[asn] = {"peers": _get_peers(asn)}
        data[asn]["customers"] = _get_customers(asn)
        data[asn]["providers"] = _get_providers(asn)
    return data


def _get_peers(asn):
    """Gets peer data for a specific asn."""

    peers = []
    sql = "SELECT * FROM peers WHERE peer_as_1=%s OR peer_as_2 = %s;"
    results = relationships_app.db.execute(sql, [asn, asn])
    for result in results:
        # Vals are ASN numbers
        for key, val in result.items():
            # We don't want to add our own ASN to the list
            if val != asn:
                peers.append(val)
    return peers


def _get_customers(asn):
    """Gets the customers of a specific asn."""

    sql = "SELECT * FROM customer_providers WHERE provider_as=%s"
    return [x["customer_as"] for x in relationships_app.db.execute(sql, [asn])]


def _get_providers(asn):
    """Gets the providers for a specific asn."""

    sql = "SELECT * FROM customer_providers WHERE customer_as=%s"
    return [x["provider_as"] for x in relationships_app.db.execute(sql, [asn])]


def _get_relationship_data():
    """Gets all relationship data.

    This was not included in the final results because it takes a while
    and would probably never be used. However, it is left here just in
    case we want to add this feature later.
    """

    sqls = {"peers": "SELECT * FROM peers;",
            "provider_customers": "SELECT * FROM customer_providers;"}
    return {k: relationships_app.db.execute(sql) for k, sql in sqls.items()}
