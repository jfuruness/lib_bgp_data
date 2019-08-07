#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for the ROAs API endpoint.

The ROAs API endpoint returns all ROAs.

Design Choices:
    -A separate blueprint was used for readability
"""

from flask import Blueprint
from flasgger import swag_from
from .api_utils import format_json

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

roas_app = Blueprint("roas_app", __name__)


@roas_app.route("/roas_data/")
@swag_from("flasgger_docs/roas.yml")
@format_json(lambda: {"description": "All ROAs used"})
def roas():
    """Returns all roas data."""

    return roas_app.db.execute("SELECT * FROM roas;")
