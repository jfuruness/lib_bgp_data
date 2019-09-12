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
    def calculate_not_bholed(self, stats, adopt_pol, p_i, t_obj, ases_dict):
        """Calculates success rates"""

        for plane in Planes.__members__.values():
            for policy in Policies.__members__.values():
                for cond in Conditions.__members__.values():
                    sim = stats[t_obj][adopt_pol][percent_i][policy.value]
                    num_cond = len(ases_dict[t_obj][policy.value][cond.value])
                    sim[plane.value][cond.value][-1] += num_cond
