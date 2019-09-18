#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ROVPP_Data_Plane_Statistics"""

# design choices - could all be in one file,
# but this was done for readability


# Include something about the assumption that if an ann 
# has a hijack its hijacked and larger proof that if ann has
# a hijack then its hijacked unless there is a data plane mechanism
# That doesnt exist in the control plane

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Reynaldo"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from copy import deepcopy
from .enums import Policies, Non_BGP_Policies, Planes, Conditions as Conds
from ..utils import error_catcher, utils


class ROVPP_Data_Plane_Stats:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['logger', 'start_time', 'stats', 'plane', 'conds_reached']

    def __init__(self, args):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        self.plane = Planes.DATA_PLANE.value
        utils.set_common_init_args(self, args, paths=False)

########################
### Helper Functions ###
########################

    def calculate_not_bholed_stats(self, ases, t_obj, atk_n, vic_n, sim):
        """Calculates statistics for data plane ASes that did not recieve hijack"""

        # If the AS didn't recieve the hijack:
        for pol in Policies.__members__.values():
            for cond in [x.value for x in [Conds.HIJACKED, Conds.NOTHIJACKED]]:
                self._calculate_specific(ases[t_obj][pol.value][cond], ases["nb"], atk_n, vic_n, sim[pol.value])

    def _calculate_specific(self, ases, all_ases, atk_n, vic_n, sim):

        conds_dict = {atk_n: Conds.HIJACKED.value,
                      vic_n: Conds.NOTHIJACKED.value,
                      -1: Conds.BHOLED.value}

        for asn, og_info in ases.items():
            debug_i = 0
            while asn not in [atk_n, vic_n, -1]:
                debug_i += 1
                if debug_i > 100:
                    self.logger.warning("current_asn" + str(asn))
                    self.logger.warning("starting_as_info" + str(og_info))
                    self.logger.warning("current as info" + str(all_ases[asn]))
                    self.logger.warning("attacker" + str(atk_n))
                    self.logger.warning("victim" + str(vic_n))
                try:
                    asn = all_ases[asn]["received_from_asn"]
                except KeyError:
                    # Blachkholed
                    asn = -1
            sim[self.plane][conds_dict[asn]][-1] += 1
