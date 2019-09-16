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

from .enums import Policies, Non_BGP_Policies, Planes, Conditions
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

        nbh = Conditions.NOT_BLACKHOLED_HIJACKED.value
        nbnh = Conditions.NOT_BLACKHOLED_NOT_HIJACKED.value
        blackholed = Conditions.BLACKHOLED.value

        # If the AS didn't recieve the hijack:
        for pol in Policies.__members__.values():
            for cond in [x for x in Conditions.__members__.values()
                         if x.value != blackholed]:
                self._calculate_specific(ases[t_obj][pol.value][cond.value],
                                         ases["all"], atk_n, vic_n, sim[pol.value])


    def _calculate_specific(self, ases, all_ases, atk_n, vic_n, sim):

        nbh = Conditions.NOT_BLACKHOLED_HIJACKED.value
        nbnh = Conditions.NOT_BLACKHOLED_NOT_HIJACKED.value
        blackholed = Conditions.BLACKHOLED.value

        for asn, og_info in ases.items():
            # SAVES THE ASES AS TRACEBACK HAPPENS
            # When it hits the end, updates all ases with those results
            traceback_as_infos = []#og_info]
            # Conditions reached at the end of the traceback
            self.conds_reached = []
            debug_i = 0
            while(len(self.conds_reached) == 0):
                debug_i += 1
                if debug_i > 100:
                    self.logger.warning(asn)
                    self.logger.warning(all_ases[asn])
                    self.logger.warning(og_info)
                    self.logger.warning(atk_n)
                    self.logger.warning(vic_n)
                if len(all_ases[asn]["data_plane_conditions"]) > 0:
                    for cond in all_ases[asn]["data_plane_conditions"]:
                        self._add_stat(sim, og_info, cond)
                # If it reaches the attackers AS or a hijacked one
                elif asn == atk_n:
                    self._add_stat(sim, og_info, nbh)
                # If it traces back to the victims AS
                elif asn == vic_n:
                    self._add_stat(sim, og_info, nbnh)
                # Else we go back another node
                else:
                    # GO BACK ANOTHER NODE!!!!
                    asn = all_ases[asn]["received_from_asn"]
                    traceback_as_infos.append(all_ases[asn])
   
            # Update the conditions reached
            self._update_ases_reached(traceback_as_infos)

    def _update_ases_reached(self, traceback_as_infos):
        """Updates all ases at the end of the traceback"""

        # Update the condition reached
        for as_info in traceback_as_infos:
            for cond in self.conds_reached:
                as_info["data_plane_conditions"].add(cond)

    def _add_stat(self, sim, _as, condition):
        """One liner for cleaner code, increments stat"""

        sim[self.plane][condition][-1] += 1
        _as["data_plane_conditions"].add(condition)
        self.conds_reached.append(condition)
