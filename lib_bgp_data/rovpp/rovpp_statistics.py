#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ROVPP_Statistics"""

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
from .rovpp_data_plane_statistics import ROVPP_Data_Plane_Statistics
from .rovpp_control_plane_statistics import ROVPP_Control_Plane_Statistics

class ROVPP_Statistics_Calculator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'stats',
                 'subprefix_hijack']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)

        # I know this could be in a dict comp but ARE YOU NUTS???
        self.stats = dict()
        for non_bgp_policy in Non_BGP_Policies.__members__.values():
            self.stats[non_bgp_policy.value] = dict()
            for percent in range(101):
                self.stats[non_bgp_policy.value][percent] = dict()
                sim = self.stats[non_bgp_policy.value][percent]
                # For each policy
                for policy in Policies.__members__.values():
                    # Set that policy to have a dict which will contain data planes
                    sim[policy.value] = dict()
                    # For each kind of data plane
                    for plane in Planes.__members__.values():
                        sim[policy.value][plane.value] = dict()
                        # For each kind of condition
                        for cond in Conditions.__members__.values():
                            # Sets rates to be a list for multiple attacks
                            sim[policy.value][plane.value][cond.value] = []


########################
### Helper Functions ###
########################

    @error_catcher()
    def calculate_stats(self, as_table, subprefix_hijack, percentage, policy):
        """Calculates success rates"""

        # Appends a zero onto all stats
        self._initialize_attack_stats(percentage, policy)
        ases_dict = self._get_ases(as_table,
                                   subprefix_hijack["more_specific_prefix"])

        # Needed for shorter lines
        # It's a reference so it's cool alright? Geez chill
        sim = self.stats[policy][percentage]
        hijacked_ases = set(ases_dict[AS_Type.RECIEVED_HIJACK.value].keys())

        self._update_ases_recieved_hijack_stats(sim, hijacked_ases, ases_dict)

        ROVPP_Control_Plane_Statistics().calculate_not_received_hijack_stats(
            as_table, sim, ases_dict)

        ROVPP_Data_Plane_Statistics().calculate_not_recieved_hijack_stats(
            ases_dict, subprefix_hijack["victim"], hijacked_ases, sim)
        pprint(sim)

    def _update_ases_recieved_hijack_stats(self, sim, hijacked, ases_dict):
        """Updates stats for all ASes that recieved the hijack"""

        # If the AS has recieved the hijack:
        for asn in hijacked:
            # Increase control plane and data plane hijacked
            for plane in Planes.__members__.values():
                # Add one to the statistic
                as_info = ases_dict[AS_Type.RECIEVED_HIJACK.value][asn]
                as_type = as_info["as_type"]
                sim[as_type][plane.value][Conditions.HIJACKED.value][-1] += 1
                #if plane.value == Planes.DATA_PLANE.value:
                as_info["data_plane_conditions"].add(Conditions.HIJACKED.value)

    @error_catcher()
    def _initialize_attack_stats(self, percentage, policy):
        """Defaults the next statistic to be 0 for everything"""

        sim = self.stats[policy][percentage]
        #I know this could be in a dict comp but ARE YOU NUTS???
        for policy in Policies.__members__.values():
            for plane in Planes.__members__.values():
                for cond in Conditions.__members__.values():
                    sim[policy.value][plane.value][cond.value].append(0)

    @error_catcher()
    def _get_ases(self, as_table, more_specific_prefix):

        # Gets all asns that where hijacked
        sql = """SELECT exr.asn, exr.prefix, exr.origin, exr.received_from_asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 INNER JOIN rovpp_ases ases
                 ON ases.asn = exr.asn
                 AND exr.prefix = %s;"""
        data = [more_specific_prefix]
        ases = {AS_Type.RECIEVED_HIJACK.value: {x["asn"]: x for x in
                                         as_table.execute(sql, data)}}

        # Get's all asns that do not have a corresponding entry for a hijack
        sql = """SELECT exr.asn, exr.prefix, exr.origin, exr.received_from_asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 LEFT JOIN (SELECT * FROM rovpp_extrapolation_results exr_og
                            WHERE exr_og.prefix = %s) exr_hijacked
                           ON exr.asn = exr_hijacked.asn
                 INNER JOIN rovpp_ases ases ON ases.asn = exr.asn
                 WHERE exr_hijacked.asn IS NULL"""

        ases[AS_Type.NOT_RECIEVED_HIJACK.value] = {x["asn"]: x for x in 
                                             as_table.execute(sql, data)}
        # Inits data plane onditions to be none
        for recieved_or_not in ases.keys():
            for asn in ases[recieved_or_not].keys():
                ases[recieved_or_not][asn]["data_plane_conditions"] = set()

        return ases
