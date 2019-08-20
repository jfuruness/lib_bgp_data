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
    def __init__(self, percents, tables, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        self.tables = tables
        # I know this could be in a dict comp but ARE YOU NUTS???
        self.stats = dict()
        for t_dict in tables:
            self.stats[t_dict["table"].name] = dict()
            for non_bgp_policy in Non_BGP_Policies.__members__.values():
                self.stats[t_dict["table"].name][non_bgp_policy.value] = dict()
                sim = self.stats[t_dict["table"].name][non_bgp_policy.value]
                for i in range(len(percents)):
                    sim[i] = dict()
                    # For each policy
                    for policy in Policies.__members__.values():
                        pol_val = policy.value
                        # Set that policy to have a dict which will contain data planes
                        sim[i][pol_val] = dict()
                        # For storing the total number of ases
                        # For each kind of data plane
                        for plane in Planes.__members__.values():
                            sim[i][pol_val][plane.value] = dict()
                            # For each kind of condition
                            for cond in Conditions.__members__.values():
                                # Sets rates to be a list for multiple attacks
                                sim[i][pol_val][plane.value][cond.value] = []


########################
### Helper Functions ###
########################

    @error_catcher()
    def calculate_stats(self, subprefix_hijack, percent_i, policy):
        """Calculates success rates"""

        for table in self.tables:
            # Needed for shorter lines
            sim = self.stats[table][policy][percent_i]

            # Appends a zero onto all stats
            self._initialize_attack_stats(sim)

            # Gets a dict of blackholed/not blackholed, and its stats
            ases_dict = self._get_ases(table)

            self._update_blackholed_ases_stats(sim, ases_dict)

            ROVPP_Control_Plane_Stats().calculate_not_bholed(sim, ases_dict)
    
            ROVPP_Data_Plane_Stats().calculate_not_bholed_stats(sim, ases_dict)

            self.logger.debug(sim)

    def _update_blackholed_ases_stats(self, sim, ases_dict):
        """Updates stats for all ASes that recieved the hijack"""

        # THIS SHOULD BE OPTIMIZED - THIS SHOULD BE A COUNT QUERY TO POSTGRES
        # NOT A FOR LOOP IN PYTHON!!!

        blackholed = Conditions.BLACKHOLED.value
        #NOTE: Does this need to be a set? take it out?
        blackholed_ases = set(ases_dict[Conditions.BLACKHOLED.value].keys())

        # Increase control plane and data plane hijacked
        for plane in Planes.__members__.values():
            for policy in Policies.__members__.values()
                num_bholed = len([x for x in blackholed_ases
                                      if ases_dict[blackholed][x]["as_type"]
                                      == policy.value])
                sim[policy.value][plane.value][blackholed][-1] += num_bholed

    @error_catcher()
    def _initialize_attack_stats(self, sim):
        """Defaults the next statistic to be 0 for everything"""

        #I know this could be in a dict comp but ARE YOU NUTS???
        for policy in Policies.__members__.values():
            for plane in Planes.__members__.values():
                for cond in Conditions.__members__.values():
                    sim[policy.value][plane.value][cond.value].append(0)

    @error_catcher()
    def _get_ases(self, table):

        nbh = Conditions.NOT_BLACKHOLED_HIJACKED.value
        nbnh = Conditions.NOT_BLACKHOLED_NOT_HIJACKED.value
        blackholed = Conditions.BLACKHOLED.value

       #NOTE: Split into multiple functions!!!!!!!!!!!!!!!!!


        # Gets all asns that where not blackholed and hijacked
        sql = """SELECT exr.asn, exr.prefix, exr.origin, exr.received_from_asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 INNER JOIN {0} ases
                     ON ases.asn = exr.asn,
                 LEFT JOIN {0} rovpp_blackholes b
                     ON b.asn = exr.asn
                 WHERE b.asn IS NULL
                     AND exr.prefix = {1};""".format(table.name,
                                                    more_specific_prefix)
        ases = {nbh: {x["asn"]: x for x in table.execute(sql)}}

        # Gets all asns that where not blackholed and hijacked
        sql = """SELECT exr.asn, exr.prefix, exr.origin, exr.received_from_asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 INNER JOIN {0} ases
                     ON ases.asn = exr.asn,
                 LEFT JOIN {0} rovpp_blackholes b
                     ON b.asn = exr.asn
                 WHERE b.asn IS NULL
                     AND exr.prefix = {1};""".format(table.name,
                                                    less_specific_prefix)
        ases = {nbnh: {x["asn"]: x for x in table.execute(sql)}}




        # Gets all asns that ARE blackholed
        sql = """SELECT DISTINCT exr.asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 INNER JOIN {0} ases
                     ON ases.asn = exr.asn,
                 INNER JOIN {0} rovpp_blackholes b
                     ON b.asn = exr.asn;""".format(table.name)
        ases[blackholed] = {x["asn"]: x for x in table.execute(sql)}

        # Inits data plane onditions to be none
        for as_type in [nbh, nbnh]:
            for asn in ases[as_type].keys():
                ases[as_type][asn]["data_plane_conditions"] = set()



        # Inits data plane conditions to contain blackholed
        for asn in ases[blackholed].keys():
            ases[blackholed][asn]["data_plane_conditions"] = set(
                Conditions.BLACKHOLED.value)

        return ases
