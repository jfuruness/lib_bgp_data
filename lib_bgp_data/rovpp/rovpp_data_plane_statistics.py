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
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from pprint import pprint
from .enums import Policies, Non_BGP_Policies, AS_Type, Planes, Conditions
from ..utils import error_catcher, utils

class ROVPP_Data_Plane_Statistics:
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

    def calculate_not_recieved_hijack_stats(self, ases_dict, victim_asn,
                                            hijacked_ases, sim):
        """Calculates statistics for data plane ASes that did not recieve hijack"""

        # If the AS didn't recieve the hijack:
        for asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value]:
            # SAVES THE ASES AS TRACEBACK HAPPENS
            # When it hits the end, updates all ases with those results
            traceback_ases = [asn]
            # Conditions reached at the end of the traceback
            self.conds_reached = []
    
            while(len(self.conds_reached) == 0):
    
                _as = self._get_as_info(asn, ases_dict) 
                # If it traces back to the victims AS
                if asn == victim_asn:
                    self._reached_victim_as(sim, _as)
    
                # If it reaches the attackers AS or a hijacked one
                elif asn in hijacked_ases:
                    self._reached_hijacked_as(sim, _as)
    
                # Or if it reaches an AS that we've seen before:
                elif len(_as["data_plane_conditions"]) > 0:
                    self._reached_previously_seen_as(sim, _as)
    
                # Else we go back another node
                else:
                    # GO BACK ANOTHER NODE!!!!
                    asn = _as["received_from_asn"]
                    traceback_ases.append(asn)
    
            # Update the conditions reached
            self._update_ases_reached(traceback_ases, ases_dict)

    def _get_as_info(self, asn, ases_dict):

        if asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value].keys():
            return ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value][asn]
        elif asn in ases_dict[AS_Type.RECIEVED_HIJACK.value].keys():
            return ases_dict[AS_Type.RECIEVED_HIJACK.value][asn]
        else:
            raise Exception("asn not in either list? {}".format(asn))


    def _reached_victim_as(self, sim, _as):
        """Occurs when a victims as is reached """

        # Increase the data plane not hijacked
        self._add_stat(sim, _as, self.plane, Conditions.NOT_HIJACKED.value)
        # Increase the data plane not hijacked not blocked
        self._add_stat(sim,
                       _as,
                       self.plane,
                       Conditions.NOT_HIJACKED_NOT_DROPPED.value)

    def _reached_hijacked_as(self, sim, _as):
        """When a hijacked AS is reached"""

        # Increase the data plane not hijacked
        self._add_stat(sim, _as, self.plane, Conditions.HIJACKED.value)

    def _reached_previously_seen_as(self, sim, _as):
        """When we reach an AS that has been previously reached"""

        for cond in _as["data_plane_conditions"]:
            self._add_stat(sim, _as, self.plane, cond)

    def _update_ases_reached(self, traceback_ases, ases_dict):
        """Updates all ases at the end of the traceback"""

        # Update the condition reached
        for asn in traceback_ases:
            # If they didn't recieve the hijack:
            if asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value]:
                # Update the conditions
                _as = ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value][asn]
                for cond in self.conds_reached:
                    _as["data_plane_conditions"].add(cond)

    @error_catcher()
    def _add_stat(self, sim, _as, plane, condition):
        """One liner for cleaner code, increments stat"""

        sim[_as["as_type"]][plane][condition][-1] += 1
        _as["data_plane_conditions"].add(condition)
        self.conds_reached.append(condition)
