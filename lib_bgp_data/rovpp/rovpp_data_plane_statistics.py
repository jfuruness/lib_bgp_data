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

from pprint import pprint
from .enums import Policies, Non_BGP_Policies, Planes, Conditions
from ..utils import error_catcher, utils

class ROVPP_Data_Plane_Stats:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'stats', 'plane',
                 'conds_reached']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        self.plane = Planes.DATA_PLANE.value

########################
### Helper Functions ###
########################

    def calculate_not_blackholed_stats(self, ases_dict, victim_asn, attacker_asn, sim):
        """Calculates statistics for data plane ASes that did not recieve hijack"""

        nbh = Conditions.NOT_BLACKHOLED_HIJACKED.value
        nbnh = Conditions.NOT_BLACKHOLED_NOT_HIJACKED.value
        # LAter on just make this one sql query
        new_dict = {}
        new_dict.update(ases_dict[nbh])
        new_dict.update(ases_dict[nbnh])

        # If the AS didn't recieve the hijack:
        for asn, og_info in new_dict.items():
            # SAVES THE ASES AS TRACEBACK HAPPENS
            # When it hits the end, updates all ases with those results
            traceback_as_infos = [og_info]
            # Conditions reached at the end of the traceback
            self.conds_reached = []
    
            while(len(self.conds_reached) == 0):
                if len(new_dict[asn]["data_plane_conditions"]) > 0:
                    for cond in new_dict[asn]["data_plane_conditions"]:
                        self._add_stat(sim, og_info, self.plane, cond)
                # If it reaches the attackers AS or a hijacked one
                elif asn == attacker_asn:
                    self._add_stat(sim, og_info, Conditions.HIJACKED.value)
                # If it traces back to the victims AS
                elif asn == victim_asn:
                    self._add_stat(sim, og_info, Conditions.NOT_HIJACKED.value)
                # Else we go back another node
                else:
                    # GO BACK ANOTHER NODE!!!!
                    asn = new_dict[asn]["received_from_asn"]
                    traceback_as_infos.append(new_dict[asn])
    
            # Update the conditions reached
            self._update_ases_reached(traceback_as_infos, new_dict)

    def _update_ases_reached(self, traceback_ases, ases_dict):
        """Updates all ases at the end of the traceback"""

        # Update the condition reached
        for as_info in traceback_ases:
            for cond in self.conds_reached:
                as_info["data_plane_conditions"].add(cond)

    @error_catcher()
    def _add_stat(self, sim, _as, condition):
        """One liner for cleaner code, increments stat"""

        sim[_as["as_type"]][self.plane][condition][-1] += 1
        _as["data_plane_conditions"].add(condition)
        self.conds_reached.append(condition)
