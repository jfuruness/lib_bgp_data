#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains useful functions to be used by applications.

Possible Future Extensions:
    -Have multiple errors with different failure messages
    -Have better logging for error failures and in general
    -Convert all stubs to parents at once
"""

import functools
from flask import jsonify, request
from copy import deepcopy
from decimal import Decimal
from ..utils import utils

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class InvalidInput(Exception):
    """Custom error for invalid input."""

    pass


def format_json(metadata_getter, *args1):
    """Decorator that formats json properly and adds metadata.

    Before the function is called the start time is recorded. Then the
    return value of the function is saved into the data part of the final
    output dictionary. Added to metadata is the metadata getter function
    that is passed into the decorator. Then the query url and seconds are
    added to the metadata. The whole dictionary is dictified to make it
    proper json format, and it is then returned.
    """

    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(*args2, **kwargs):
            # Inside the decorator
            try:
                start = utils.now()
                # Get the results from the function
                results = func(*args2, **kwargs)
                # Save the results to data, and use metadata func for metadata
                final = {"data": results, "metadata": metadata_getter(*args1)}
                api_url = "https://bgpforecast.uconn.edu"
                meta = final["metadata"]
                # Add query url to metadata
                meta["query_url"] = api_url + request.path
                # Add seconds to metadata
                meta["seconds"] = (utils.now() - start).total_seconds()
                # dictify for proper json format then jsonify it and return
                return jsonify(dictify(final))
            except InvalidInput:
                # If there is an invalid input error, return this:
                return jsonify({"ERROR": "Invalid input"})
            except Exception as e:
                # Never allow the API to crash. This should record errors
                print(e)
                return jsonify({"ERROR": "Please contact jfuruness@gmail.com"})
        return function_that_runs_func
    return my_decorator


def validate_asns(asns, db):
    """Validates asn input and converts stubs to parents."""

    try:
        # Make sure all asns are ints
        asns = [int(asn) for asn in deepcopy(asns)]
        # Convert stubs to parents
        return convert_stubs_to_parents(asns, db)
    except ValueError:
        # If asns are not ints raise invalid input error
        raise InvalidInput


def get_policies():
    """Returns a list of valid policies.

    This can be changed easily to change the policies used everywhere.
    """

    return {"invalid_asn", "invalid_length", "rov"}


def validate_policies(policies):
    """Validates all policies. Raises InvalidInput if invalid"""

    # Set all to be all valid policies
    if "all" in policies:
        policies = get_policies()
    for policy in policies:
        # If the policies are not in this set, raise invalid input
        if policy not in get_policies().union({"all"}):
            raise InvalidInput
    return policies


def convert_stubs_to_parents(asns, db):
    """Converts all stubs to parents.

    For our data, stub ASes have the same data as there parents. Because
    of this, we do not store stub data, and instead copy it from the
    parents.
    """

    list_of_asns = []
    sql = "SELECT * FROM stubs WHERE stub_asn=%s"
    for asn in asns:
        results = db.execute(sql, [asn])
        # It is not a stub, so append the asn
        if len(results) == 0:
            list_of_asns.append(asn)
        # It is a stub. Append the parent
        else:
            list_of_asns.append(results[0]["parent_asn"])
    return list_of_asns


def dictify(result):
    """Formats dictionary properly for jsonfication recursively."""

    if not isinstance(result, dict):
        # Dictify everything in the list
        if isinstance(result, list):
            return [dictify(x) for x in result]
        # Postgres sometimes returns decimal. Convert to a float
        if isinstance(result, Decimal):
            return float(result)
        return result
    # Gets rid of the RealDictRow from postgres
    formatted = {key: dictify(val) for key, val in result.items()}
    # Make urls full urls
    if "url" in formatted:
        formatted["url"] = "https://bgpstream.com{}".format(formatted["url"])
    return formatted
