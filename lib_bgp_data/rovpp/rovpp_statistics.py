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
        ases_dict = self._get_ases(subp_hijack["more_specific_prefix"],
                                   subp_hijack["expected_prefix"])
        for t_obj in self.tables:
            # Needed for shorter lines
            sim = self.stats[t_obj][adopt_policy][percent_i]
            # Appends a zero onto all stats
            self._initialize_attack_stats(sim)

            self._update_blackholed_ases_stats(sim, ases_dict)

            ROVPP_Control_Plane_Stats().calculate_not_bholed(self.stats,
                                                             adopt_policy,
                                                             percent_i,
                                                             t_obj,
                                                             ases_dict)

            ROVPP_Data_Plane_Stats().calculate_not_bholed_stats(ases_dict,
                                                                t_obj
                                                                subp_hijack["attacker"],
                                                                subp_hijack["victim"],
                                                                sim)
            self.logger.debug(sim)

    def _update_blackholed_ases_stats(self, adopt_pol, percent_i, ases_dict):
        """Updates stats for all ASes that recieved the hijack"""

        # THIS SHOULD BE OPTIMIZED - THIS SHOULD BE A COUNT QUERY TO POSTGRES
        # NOT A FOR LOOP IN PYTHON!!!

        blackholed = Conditions.BLACKHOLED.value

        # Increase control plane and data plane hijacked
        for t_obj in self.tables:
            for plane in Planes.__members__.values():
                for policy in Policies.__members__.values():
                sim = self.stats[t_obj][adopt_pol][percent_i]
                num_bholed = len(ases_dict[t_obj][policy.value][blackholed])
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
    def _get_ases(self, hijack_p, victim_p):

        nbh = Conditions.NOT_BLACKHOLED_HIJACKED.value
        nbnh = Conditions.NOT_BLACKHOLED_NOT_HIJACKED.value
        blackholed = Conditions.BLACKHOLED.value

        ases_dict = dict()
        tables = self.tables
        # Get blackholed ases
        # for all blackholed ases, group by subtable
        sql = """WITH bholed AS (
                        SELECT exrf.asn FROM
                            rovpp_extrapolation_results_filtered exrf
                        LEFT JOIN rovpp_blackholes b
                            ON b.asn = exrf.asn),"""
        for t_obj in tables:
            sql += """ {0}_dropped AS (DROP TABLE IF EXISTS {0}_bholed), 
                   {0}_bholed AS (CREATE TABLE {0}_bholed AS (
                   SELECT b.asn, a.as_type FROM bholed b
                       INNER JOIN {0} a
                       ON {0}.asn = b.asn),""".format(t_obj.table.name)
        tables[0].table.execute(sql[:-1] + " NULL;")

        for t_obj in tables:
            sql = """SELECT b.asn FROM {}_bholed b
                  WHERE as_type = """.format(t_obj.table.name)
            ases_dict[t_obj] = dict()
            for pol in Policies.__members__.values():
                ases_dict[t_obj][pol.value] = dict()
                ases_dict[t_obj][pol.value][blackholed] = \
                    {x["asn"]: {**x + **{"data_plane_conditions":
                                         {blackholed})}}
                     for x in tables[0].table.execute(sql + pol.value)}


        # CHANGE THIS TO GET ALL THE SPECIFIC DICTS FOR CTRL AND DATA PLANE FOR EACH POL!!!!!
        # can add all later for iterations
        # NOTE: NOW HAVE SUBTABLES DICT AND AN ALL DICT!!!i
        sql = """WITH not_bholed AS (
                    SELECT exrf.asn, exrf.recieved_from_asn,
                            exrf.prefix, ases.as_type
                        FROM rovpp_extrapolation_results_filtered exrf
                    LEFT JOIN rovpp_blackholes b
                        ON b.asn = exrf.asn
                    WHERE b.asn IS NULL),
                nbh AS (
                    SELECT nb.asn, nb.recieved_from_asn, nb.as_type
                        FROM not_bholed nb
                    WHERE nb.prefix = %s),
                nbnh AS (
                    SELECT nb.asn, nb.recieved_from_asn, nb.as_type
                        FROM not_bholed nb
                    WHERE nb.prefix = %s),"""
        for t_obj in tables:
            for cond in ['nbh', 'nbnh']:
                sql += """{1}_{0}_dropped AS (
                           DROP TABLE IF EXISTS {1}_{0}_dropped),
                       {1}_{0} AS (
                       CREATE TABLE {1}_{0} AS (
                           SELECT {1}.asn, {1}.recieved_from_asn, {1}.as_type
                               FROM {1}
                           INNER JOIN {0}
                               ON {0}.asn = {1}.asn)
                                   ),""".format(t_obj.table.name)
            sql = sql[:-1] + " NULL;"
            tables[0].table.execute(sql)


        for t_obj in tables:
            for cond in ['nbh', 'nbnh']:
                for pol in Policies.__members__.values:
                    sql = """SELECT * FROM {1}_{0}
                          WHERE {1}_{0}.as_type
                          = {2}""".format(t_obj.table.name, cond, pol.value)
                    if cond == 'nbh':
                        tcond = nbh
                    elif cond == 'nbnh':
                        tcond = nbnh
                    ases_dict[t_obj][pol.value][tcond] = \
                        {x["asn"]: {**x + **{"data_plane_conditions": set()}}
                         for x in tables[0].table.execute(sql)}

    ases_dict["all"] = dict()
    for t_obj in tables:
        for cond in [nbh, nbnh, blackholed]:
            for pol in Policies.__members__.values:
                ases_dict["all"].update(ases_dict[t_obj][pol.value][cond])
        return ases
