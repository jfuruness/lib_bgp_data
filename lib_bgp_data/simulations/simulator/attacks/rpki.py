#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class RPKI.

This class is used to store information about RPKI.
This can be used to determine announcement validity
The reason we aren't doing this in SQL is because
typical case is 1 ann, and we want speed

See README for in depth instruction
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from netaddr import IPNetwork


class RPKI:
    """Contains info about RPKI

    since typical use case is 1 ann, we don't use SQL
    """

    def __init__(self, roas: list):
        """Save roas"""

        self.roas = roas

    def check_ann(self, prefix: str, origin: int):
        """Checks announcement validity. Returns worst validity found

        NOTE: if you end up doing this with lots of announcements,
        This should probably be done in SQL
        """

        # Default validity
        worst_validity = ROA_Validity.UNKNOWN
        # Convert to proper datatype
        prefix = IPNetwork(prefix)
        # List of ROA objects
        for roa in self.roas:
            # Get validity
            validity = roa.check_validity(prefix, origin)
            # If valid, return
            if validity == ROA_Validity.VALID:
                return validity
            # Continue looking for worst validity possible
            else:
                # If validity is worse, set worst_validity
                # valid < unknown < invalid by asn or length < invalid by all
                if worst_validity.value > validity.value:
                    worst_validity = validity

        return worst_validity
