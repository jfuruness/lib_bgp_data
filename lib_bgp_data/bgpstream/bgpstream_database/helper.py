#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a function that prints and raises formatted errors"""

import pprint


def format_error(self, err_info, error):
    """Prints errors with most local variables and raises"""
    # Hacky ik
    for key, val in err_info.items():
        if key == 'sql':
            pass
        elif key == 'self':
            pass
        elif isinstance(val, dict) or isinstance(val, list):
            print(key)
            pprint.pprint(val)
        else:
            print(key)
            print(val)
    raise error
