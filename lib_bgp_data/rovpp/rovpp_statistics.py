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
from .enums import Policies, Non_BGP_Policies, Planes, Conditions
from ..utils import error_catcher, utils
from .rovpp_data_plane_statistics import ROVPP_Data_Plane_Stats
from .rovpp_control_plane_statistics import ROVPP_Control_Plane_Stats

class ROVPP_Statistics_Calculator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    @error_catcher()
    def __init__(self, percents, tables, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        self.tables = tables
        # I know this could be in a dict comp but ARE YOU NUTS???
        self.stats = dict()
        for t_obj in tables:
            self.stats[t_obj] = dict()
            for non_bgp_policy in Non_BGP_Policies.__members__.values():
                self.stats[t_obj][non_bgp_policy.value] = dict()
                sim = self.stats[t_obj][non_bgp_policy.value]
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
    def calculate_stats(self, subp_hijack, percent_i, adopt_policy):
        """Calculates success rates"""

        self._filter_exr(self.tables[0].table,
                         subp_hijack["more_specific_prefix"],
                         subp_hijack["expected_prefix"])
        tases_dict = self._get_all_ases()
        for t_obj in self.tables:
            # Needed for shorter lines
            sim = self.stats[t_obj][adopt_policy][percent_i]
            # Appends a zero onto all stats
            self._initialize_attack_stats(sim)

            # Gets a dict of blackholed/not blackholed, and its stats
            ases_dict = self._get_ases(t_obj.table,
                                       subp_hijack["more_specific_prefix"],
                                       subp_hijack["expected_prefix"],
                                       tases_dict)

            self._update_blackholed_ases_stats(sim, ases_dict)

            ROVPP_Control_Plane_Stats().calculate_not_bholed(sim, ases_dict)

            ROVPP_Data_Plane_Stats().calculate_not_bholed_stats(ases_dict,
                                                                subp_hijack["attacker"],
                                                                subp_hijack["victim"],
                                                                sim)
            self.logger.debug(sim)

    def _get_all_ases(self):
        sql = """SELECT exrf.asn, exrf.prefix, exrf.origin, exrf.received_from_asn,
                  COALESCE("""
        for t_obj in self.tables:
            sql += "{}.as_type, ".format(t_obj.table.name)
        sql = sql[:-2]
        sql += ") AS as_type FROM rovpp_extrapolation_results_filtered exrf "
        for t_obj in self.tables:
            sql += "LEFT JOIN {0} ON {0}.asn = exrf.asn ".format(t_obj.table.name)
        sql += ";"
        print(sql)
        return {"all": {x["asn"]: {**x, **{"data_plane_conditions": set()}}
                       for x in self.tables[0].table.execute(sql)}}


    def _update_blackholed_ases_stats(self, sim, ases_dict):
        """Updates stats for all ASes that recieved the hijack"""

        # THIS SHOULD BE OPTIMIZED - THIS SHOULD BE A COUNT QUERY TO POSTGRES
        # NOT A FOR LOOP IN PYTHON!!!

        blackholed = Conditions.BLACKHOLED.value
        #NOTE: Does this need to be a set? take it out?
        blackholed_ases = ases_dict[Conditions.BLACKHOLED.value]

        # Increase control plane and data plane hijacked
        for plane in Planes.__members__.values():
            for policy in Policies.__members__.values():
                num_bholed = len([x for x in blackholed_ases
                                  if ases_dict["all"][x]["as_type"]
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
    def _filter_exr(self, table, hijack_p, victim_p):
        table.execute("DROP TABLE IF EXISTS rovpp_extrapolation_results_filtered")

        sql = """CREATE TABLE rovpp_extrapolation_results_filtered AS (
              SELECT DISTINCT ON (exr.asn) exr.asn, COALESCE(exrh.prefix, exrnh.prefix) AS prefix,
                     COALESCE(exrh.origin, exrnh.origin) AS origin,
                     COALESCE(exrh.received_from_asn, exrnh.received_from_asn)
                         AS received_from_asn
                  FROM rovpp_extrapolation_results exr
              LEFT JOIN rovpp_extrapolation_results exrh
                  ON exrh.asn = exr.asn AND exrh.prefix = %s
              LEFT JOIN rovpp_extrapolation_results exrnh
                  ON exrnh.asn = exr.asn AND exrnh.prefix = %s);"""

        table.execute(sql, [hijack_p, victim_p])


    @error_catcher()
    def _get_ases(self, table, hijack_p, victim_p, ases):

        nbh = Conditions.NOT_BLACKHOLED_HIJACKED.value
        nbnh = Conditions.NOT_BLACKHOLED_NOT_HIJACKED.value
        blackholed = Conditions.BLACKHOLED.value


        # Gets all asns that where not blackholed and hijacked
        sql = """SELECT exrf.asn, exrf.prefix, exrf.origin, exrf.received_from_asn,
                 ases.as_type FROM rovpp_extrapolation_results_filtered exrf
                 INNER JOIN {0} ases
                     ON ases.asn = exrf.asn
                 LEFT JOIN rovpp_blackholes b
                     ON b.asn = exrf.asn
                 WHERE b.asn IS NULL
                     AND exrf.prefix = """.format(table.name)
        sql += "%s;"

        ases[nbh] = {x["asn"] for x in table.execute(sql, [hijack_p])}

        ases[nbnh] = {x["asn"] for x in table.execute(sql, [victim_p])}

        # Gets all asns that ARE blackholed
        sql = """SELECT DISTINCT exr.asn,
                 ases.as_type FROM rovpp_extrapolation_results exr
                 INNER JOIN {0} ases
                     ON ases.asn = exr.asn
                 INNER JOIN rovpp_blackholes b
                     ON b.asn = exr.asn;""".format(table.name)
        ases[blackholed] = {x["asn"] for x in table.execute(sql)}

        # Inits data plane conditions to contain blackholeid
        for asn in ases[blackholed]:
            ases["all"][asn]["data_plane_conditions"].add(blackholed)

        return ases
