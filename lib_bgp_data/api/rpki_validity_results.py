#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for the extrapolator API endpoint.

The extrapolator API endpoint returns the local RIB(s) for ASNs,
discluding all announcements that do not have ROAs.

Design Choices:
    -A separate blueprint was used for readability
    -Data is not decoded for time
"""

from flask import Blueprint
from flasgger import swag_from
from .api_utils import format_json
from ..rpki_validator import RPKI_Validator

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

RPKI_app = Blueprint("RPKI_app", __name__)


def get_rpki_validator_metadata():
    """Gets the RPKI metadata."""

    return {"description": "Validity data from the RPKI validator.",
            "decoder": RPKI_Validator.get_validity_dict()}


@RPKI_app.route("/rpki_validator_data/")
@swag_from("flasgger_docs/rpki_validator.yml")
@format_json(get_rpki_validator_metadata)
def rpki_validator_data():
    """Gets all the RPKI validity data. Data is not decoded for time."""

    return RPKI_app.db.execute("SELECT * FROM rov_validity LIMIT 5;")
