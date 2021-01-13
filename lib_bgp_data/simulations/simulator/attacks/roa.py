#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class ROA.

This class is used to store information about a ROA.
For simplicity, max_length = prefix_length

See README for in depth instruction
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


from netaddr import IPNetwork

from ....utils.base_classes import ROA_Validity


class ROA:
    """Stores information for a ROA"""

    def __init__(self, prefix: IPNetwork, origin: int, max_len=None):
        """Inits prefix, origin, and max length

        max length defaults to prefix length if not specified
        """

        self.prefix = IPNetwork(prefix)
        self.origin = origin
        # Default to prefix max len
        self.max_len = max_len if max_len else self.prefix.prefixlen

    def check_validity(self, prefix: IPNetwork, origin: int):
        """Checks the validity of an announcement"""

        assert isinstance(prefix, IPNetwork), "Convert to IPNetwork"

        # If a prefix is within our prefix, this ROA matter
        if prefix in self.prefix:
            # Get length and origin validity
            length = True if prefix.prefixlen <= self.max_len else False
            correct_origin = True if origin == self.origin else False
            # If all are correct
            if length and correct_origin:
                return ROA_Validity.VALID
            # If none are correct
            elif not length and not correct_origin:
                return ROA_Validity.INVALID_BY_ALL
            # If length is not correct
            elif not length:
                return ROA_Validity.INVALID_BY_LENGTH
            # If origin is not correct
            else:
                return ROA_Validity.INVALID_BY_ORIGIN
        # Prefix is not contained with ROA, unknown
        else:
            return ROA_Validity.UNKNOWN
