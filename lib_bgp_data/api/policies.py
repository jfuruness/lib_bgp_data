#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the blueprint for a policy API endpoint.

Design Choices:
    -A separate blueprint was used for readability
"""
from flask import Blueprint
from flasgger import swag_from
from .api_utils import validate_asns, validate_policies, format_json, dictify

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


policies_app = Blueprint("policies_app", __name__)


def get_policy_descriptions():
    """Gets the descriptions for each policy."""

    return {"rov": ("Block route announcements using standard"
                    " Resource Certification (RPKI) Route Origin"
                    " Validation (ROV) as defined in RFC 6811"),
            "invalid_asn": ("Block route announcements only when"
                            " the originating AS is in conflict"
                            " with a Route Origin Authorization"
                            " (ROA). Announcements containing"
                            " prefixes exceeding the maximum length"
                            " authorized by a ROA are allowed."),
            "invalid_length": ("Block route announcements only"
                               " when the length of the announced"
                               " prefix exceeds the maximum length"
                               " authorized by a ROA."
                               " Announcements originating from an"
                               " AS that is not authorized to do"
                               " so are allowed.")}


def get_policy_metadata():
    """Gets the metadata for the policies route."""

    metadata = {"disclaimers": ("All announcements and hijacks in this"
                                " dataset are covered by a ROA. In other"
                                " words, the prefixes are a subset of a"
                                " ROA.")}
    metadata.update(get_policy_descriptions())
    return metadata


@policies_app.route("/policy_stats/<list:asns>/<list:policies>/")
@swag_from("flasgger_docs/policy_stats.yml")
@format_json(get_policy_metadata)
def policy_stats(asns, policies):
    """Returns the policy statistics and hijack data for asns."""

    # Validate asns and convert to parents
    asns = validate_asns(asns, policies_app.db)
    # Validate policies
    policies = validate_policies(policies)
    results = {policy: {} for policy in policies}
    for policy in policies:
        for asn in asns:
            # Gets overall statistics for the policy
            results[policy][str(asn)] = get_stats(asn, policy)
            # Gets the hijack data for the policy
            results[policy][str(asn)].update(get_hijack_data(asn, policy))
        # Gets average data over all asns for the policy
        results[policy].update(get_avg_stats(dictify(results[policy]), asn))
    return results


def get_stats(asn, policy):
    """Gets general statistics for each policy/asn."""

    sql = "SELECT * FROM {} WHERE parent_asn={}".format(policy, asn)
    results = policies_app.db.execute(sql)
    if len(results) == 0:
        results = [{}]
    return results[0]


def get_avg_stats(policy_dict, asn):
    """Gets the average statistics among all asns for each policy."""

    num_asns = len(policy_dict)
    average = {}
    # For each column/data point:
    for key in policy_dict[str(asn)]:
        # Ignore parent_asn and hijack data, since avg is meaningless
        if key == "parent_asn" or "hijack_data" in key:
            continue
        # Sums up the data point for all asns and divides by num_asns
        average[key] = sum([policy_dict[x][key] for x in policy_dict])/num_asns
    return {"aggregate_average_data": average}


def get_hijack_data(asn, pol):
    """Gets the hijack data for an asn and policy pol."""

    info = {}
    og_sql = """SELECT iabh.prefix, iabh.origin, iabh.url
             FROM input iabh
               LEFT OUTER JOIN
                 (SELECT * FROM extrapolation_inverse_results
                     WHERE asn={}) exr
             ON exr.prefix = iabh.prefix AND exr.origin = iabh.origin
             WHERE exr.prefix IS NULL AND exr.origin IS NULL;""".format(asn)

    # ROV's hijack data is just the sum of invalid_asn and invalid_length
    policies = ["invalid_asn", "invalid_length"] if pol == "rov" else [pol]

    for policy in policies:
        # What to call the hijacks
        p_descr = "{}_hijack_data".format(policy)
        info[p_descr] = {}
        # The two kinds of hijack data
        for y in ["blocked_hijacked", "not_blocked_hijacked"]:
            sql = og_sql.replace("input", "{}_{}".format(policy, y))
            info[p_descr]["{}_info".format(y)] = [x for x in
                                                  policies_app.db.execute(sql)]
    return info
