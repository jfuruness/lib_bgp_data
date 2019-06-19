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
        for _non_bgp_policy in Non_BGP_Policies.__members__.values():
            non_bgp_policy = _non_bgp_policy.value
            self.stats[non_bgp_policy] = dict()
            for percent in range(101):
                self.stats[non_bgp_policy][percent] = dict()
                sim = self.stats[non_bgp_policy][percent]
                # For each policy
                for _policy in Policies.__members__.values():
                    policy = _policy.value
                    # Set that policy to have a dict which will contain data planes
                    sim[policy] = dict()
                    # For each kind of data plane
                    for _plane in Planes.__members__.values():
                        plane = _plane.value
                        sim[policy][plane] = dict()
                        # For each kind of condition
                        for _cond in Conditions.__members__.values():
                            cond = _cond.value
                            # Sets rates to be a list for multiple attacks
                            sim[policy][plane][cond] = []


########################
### Helper Functions ###
########################

    @error_catcher()
    def calculate_stats(self, as_table, subprefix_hijack, percentage, policy):
        """Calculates success rates"""


        self.subprefix_hijack = subprefix_hijack
        # self.stats[percent][policy][plane][cond] = []
        # Appends a zero onto all stats
        self._initialize_attack_stats(percentage, policy)
        # Returns a dictionary of ases by policy in the enum policies
        # Filters out the attacker and the victim from the results 
        ases_dict = self._get_ases(as_table, subprefix_hijack)

        # Needed for shorter lines
        # It's a reference so it's cool alright? Geez chill
        sim = self.stats[policy][percentage]

        self._update_ases_recieved_hijack_stats(sim, ases_dict)
        self._update_ases_not_recieved_hijack_stats(sim, ases_dict, as_table)
        pprint(self.stats[policy][percentage])

    def _update_ases_recieved_hijack_stats(self, sim, ases_dict):
        """Updates stats for all ASes that recieved the hijack"""

        # If the AS has recieved the hijack:
        for asn in ases_dict[AS_Type.RECIEVED_HIJACK.value]:
            # Increase control plane and data plane hijacked
            for plane in Planes.__members__.values():
                # Add one to the statistic
                self._add_stat(sim,
                               ases_dict[AS_Type.RECIEVED_HIJACK.value][asn],
                               plane.value,
                               Conditions.HIJACKED.value)

    def _update_ases_not_recieved_hijack_stats(self, sim, ases_dict, as_table):

        blackholed_asns = self._get_blackhole_asns(as_table)

        hijacked_ases = set(ases_dict[AS_Type.RECIEVED_HIJACK.value].keys())
        hijacked_ases.add(self.subprefix_hijack["attacker"])

        # If the AS didn't recieve the hijack:
        for asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value]:
            # First increase the control plane not hijacked

            self._add_stat(sim,
                           ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value][asn],
                           Planes.CONTROL_PLANE.value,
                           Conditions.NOT_HIJACKED.value)
            # Then increase the control plane not hijacked not droped
            if asn in blackholed_asns:
                self._add_stat(sim,
                               ases_dict[
                                   AS_Type.NOT_RECIEVED_HIJACK.value][asn],
                               Planes.CONTROL_PLANE.value,
                               Conditions.DROPPED.value)

            else:
                self._add_stat(sim,
                               ases_dict[
                                   AS_Type.NOT_RECIEVED_HIJACK.value][asn],
                               Planes.CONTROL_PLANE.value,
                               Conditions.NOT_HIJACKED_NOT_DROPPED.value)
            # trace backwards and calculate data plan stats
            self._traceback(sim,
                            asn,
                            ases_dict,
                            self.subprefix_hijack["attacker"],
                            self.subprefix_hijack["victim"],
                            hijacked_ases)

    @error_catcher()
    def _traceback(self, sim, asn, ases_dict, attacker_asn, victim_asn,
                   hijacked_ases):

        # SAVES THE ASES AS TRACEBACK HAPPENS
        # When it hits the end, updates all ases with those results
        traceback_ases = [asn]
        # Conditions reached at the end of the traceback
        conds_reached = []

        while(len(conds_reached) == 0):

            if asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value].keys():
                _as = ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value][asn]
            elif asn in ases_dict[AS_Type.RECIEVED_HIJACK.value].keys():
                _as = ases_dict[AS_Type.RECIEVED_HIJACK.value][asn]
            else:
                print(asn)
                print(attacker_asn)
                print(victim_asn)
                raise Exception("asn not in either list? {}".format(asn))

            # If it traces back to the victims AS
            if asn == victim_asn:
                self._reached_victim_as(sim, _as, conds_reached)

            # If it reaches the attackers AS or a hijacked one
            elif asn in hijacked_ases:
                self._reached_hijacked_as(sim, _as, conds_reached)

            # Or if it reaches an AS that we've seen before:
            elif len(_as["data_plane_conditions"]) > 0:
                self._reached_previously_seen_as(sim, _as, conds_reached)

            # Else we go back another node
            else:
                # GO BACK ANOTHER NODE!!!!
                asn = _as["received_from_asn"]
                traceback_ases.append(asn)

        # Update the conditions reached
        self._update_ases_reached(traceback_ases, ases_dict, conds_reached)

    def _reached_victim_as(self, sim, _as, conditions_reached):
        """Occurs when a victims as is reached """

        # Increase the data plane not hijacked
        self._add_stat(sim,
                       _as,
                       Planes.DATA_PLANE.value,
                       Conditions.NOT_HIJACKED.value)
                # Increase the data plane not hijacked not blocked
        self._add_stat(sim,
                       _as,
                       Planes.DATA_PLANE.value,
                       Conditions.NOT_HIJACKED_NOT_DROPPED.value)
        conditions_reached.append(Conditions.NOT_HIJACKED.value)
        conditions_reached.append(Conditions.NOT_HIJACKED_NOT_DROPPED.value)

    def _reached_hijacked_as(self, sim, _as, conditions_reached):
        """When a hijacked AS is reached"""

        # Increase the data plane not hijacked
        self._add_stat(sim,
                       _as,
                       Planes.DATA_PLANE.value,
                       Conditions.HIJACKED.value)
        conditions_reached.append(Conditions.HIJACKED.value)

    def _reached_previously_seen_as(self, sim, _as, conditions_reached):
        """When we reach an AS that has been previously reached"""

        for cond in _as["data_plane_conditions"]:
            self._add_stat(sim, _as, Planes.DATA_PLANE.value, cond)
            conditions_reached.append(cond)

    def _update_ases_reached(self, traceback_ases, ases_dict, conds_reached):
        """Updates all ases at the end of the traceback"""

        # Update the condition reached
        for asn in traceback_ases:
            # If they didn't recieve the hijack:
            if asn in ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value].keys():
                # Update the conditions
                _as = ases_dict[AS_Type.NOT_RECIEVED_HIJACK.value][asn]
                for cond in conds_reached:
                    _as["data_plane_conditions"].add(cond)


    @error_catcher()
    def _initialize_attack_stats(self, percentage, policy):
        """Defaults the next statistic to be 0 for everything"""

        sim = self.stats[policy][percentage]
        #I know this could be in a dict comp but ARE YOU NUTS???
        for policy in Policies.__members__.values():
            for plane in Planes.__members__.values():
                for cond in Conditions.__members__.values():
                    sim[policy.value][plane.value][cond.value].append(0)

    def _get_blackhole_asns(self, as_table):
        """Gets all blackhole asns"""

        return [x["asn"] 
                for x in as_table.execute("SELECT * FROM rovpp_blackholes;")]

    @error_catcher()
    def _get_ases(self, as_table, subprefix_hijack):
        """EXCLUDES ATTACKER AND VICTIM ASES"""

        # Gets all asns that where hijacked
        sql = """SELECT exr.asn, exr.prefix, exr.origin, exr.received_from_asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 INNER JOIN rovpp_ases ases
                 ON ases.asn = exr.asn
                 AND exr.prefix = %s;"""
        data = [subprefix_hijack["more_specific_prefix"]]
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

    @error_catcher()
    def _add_stat(self, sim, _as, plane, condition):
        """One liner for cleaner code, increments stat"""

        sim[_as["as_type"]][plane][condition][-1] += 1

        if plane == Planes.DATA_PLANE.value:
            _as["data_plane_conditions"].add(condition)
