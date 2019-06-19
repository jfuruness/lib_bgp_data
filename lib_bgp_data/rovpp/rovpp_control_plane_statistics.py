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
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from pprint import pprint
from .enums import Policies, Non_BGP_Policies, AS_Type, Planes, Conditions
from ..utils import error_catcher, utils

class ROVPP_Control_Plane_Statistics:
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
    def calculate_not_received_hijack_stats(self, as_table, sim, ases_dict):
        """Calculates success rates"""

        blackholed_asns = self._get_blackhole_asns(as_table)

        # If the AS didn't recieve the hijack:
        for asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value]:
            # First increase the control plane not hijacked

            _as = ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value][asn]

            self._add_stat(sim, _as, self.plane, Conditions.NOT_HIJACKED.value)

            # Then increase the control plane not hijacked not droped
            if asn in blackholed_asns:
                self._add_stat(sim, _as, self.plane, Conditions.DROPPED.value)

            else:
                self._add_stat(sim,
                               _as,
                               self.plane,
                               Conditions.NOT_HIJACKED_NOT_DROPPED.value)

    def _get_blackhole_asns(self, as_table):
        """Gets all blackhole asns"""

        return set([x["asn"] 
                for x in as_table.execute("SELECT * FROM rovpp_blackholes;")])

    @error_catcher()
    def _add_stat(self, sim, _as, plane, condition):
        """One liner for cleaner code, increments stat"""

        sim[_as["as_type"]][plane][condition][-1] += 1
