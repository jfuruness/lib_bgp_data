#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ROVPP_Control_Plane_Statistics"""

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

from pprint import pprint
from .enums import Policies, Non_BGP_Policies, Planes, Conditions
from ..utils import error_catcher, utils

class ROVPP_Control_Plane_Stats:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'plane']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        self.plane = Planes.CONTROL_PLANE.value

########################
### Helper Functions ###
########################

    @error_catcher()
    def calculate_not_bholed_stats(self, sim, ases_dict):
        """Calculates success rates"""

        #### NOTE: THIS SHOULD BE SQL AGAIN!!! OPTIMIZE SO THAT FOR ECAH
        # SUBTABLE YOU CAN ONLY HAVE ONE POLICY, bgp or non bgp, then do
        # this all in sql!!!!!

        for _cond in Conditions.__members__.values():
            cond = _cond.value
            if cond == Conditions.BLACKHOLED.value:
                continue  # We did these already
            #NOTE: does this need to be a set? take this out!
            cond_ases = set(ases_dict[cond].keys())
            for policy in Policies.__members__.values():
                # Total number of ases for that cond with that policy
                num = len([x for x in cond_ases
                           if ases_dict[cond][x]["as_type"] == policy.value])
                sim[policy.value][plane.value][cond][-1] += num
