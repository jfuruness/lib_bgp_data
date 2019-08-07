#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for the extrapolator API endpoint.

The extrapolator API endpoint returns the local RIB(s) for ASNs,
discluding all announcements that do not have ROAs.

Design Choices:
    -A separate blueprint was used for readability
"""

from flask import Blueprint
from flasgger import swag_from
from .api_utils import format_json, validate_asns

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


extrapolator_engine_results_app = Blueprint("extrapolator_engine_results_app",
                                            __name__)


def get_extrapolator_metadata():
    """Returns extrapolator specific metadata.

    Used in the format_json decorator.
    """

    extrapolator_description = ("All prefix origin pairs within the"
                                " local RIB(s) according to the"
                                " extrapolator-engine")
    return {"description": extrapolator_description}


@extrapolator_engine_results_app.route("/extrapolator_data/<list:asns>/")
@swag_from("flasgger_docs/extrapolator.yml")
@format_json(get_extrapolator_metadata)
def extrapolation(asns):
    """Uninverts an ASN.

    Returns all announcements that have ROAs and were kept by that asn.
    """

    db = extrapolator_engine_results_app.db
    sql = """SELECT DISTINCT mrt.prefix, mrt.origin FROM mrt_w_roas mrt
          LEFT OUTER JOIN
              (SELECT prefix, origin
                  FROM extrapolation_inverse_results
              WHERE asn=%s) exr
          ON mrt.prefix = exr.prefix AND mrt.origin = exr.origin
          WHERE exr.prefix IS NULL OR exr.origin IS NULL;"""
    return {x: db.execute(sql, [x]) for x in validate_asns(asns, db)}
