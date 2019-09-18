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
from .enums import Policies, Non_BGP_Policies, Planes, Top_Node_Policies, Hijack_Types, Conditions as Conds
from ..utils import error_catcher, utils
from .rovpp_data_plane_statistics import ROVPP_Data_Plane_Stats
from .rovpp_control_plane_statistics import ROVPP_Control_Plane_Stats

class ROVPP_Statistics_Calculator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    def __init__(self, args, percents, tables):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args, paths=False)
        self.args = args
        self.tables = tables
        # I know this could be in a dict comp but ARE YOU NUTS???
        self.stats = dict()
        for htype in [x.value for x in Hijack_Types.__members__.values()]:
            self.stats[htype] = dict()
            for pol in [x.value for x in Top_Node_Policies.__members__.values()]:
                self.stats[htype][pol] = dict()
                for t_obj in tables:
                    self.stats[htype][pol][t_obj] = dict()
                    for non_bgp_policy in Non_BGP_Policies.__members__.values():
                        self.stats[htype][pol][t_obj][non_bgp_policy.value] = dict()
                        sim = self.stats[htype][pol][t_obj][non_bgp_policy.value]
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
                                    for cond in Conds.__members__.values():
                                        # Sets rates to be a list for multiple attacks
                                        sim[i][pol_val][plane.value][cond.value] = []


########################
### Helper Functions ###
########################

    @utils.run_parser(paths=False)
    def calculate_stats(self, subp_hijack, percent_i, adopt_pol, top_nodes_pol, hijack_type):
        """Calculates success rates"""

        start = utils.now()
        self._filter_exr(self.tables[0].table,
                         subp_hijack["more_specific_prefix"],
                         subp_hijack["expected_prefix"])
        ases_dict = self._get_ases(subp_hijack["more_specific_prefix"],
                                   subp_hijack["expected_prefix"])
        for t_obj in self.tables:
            # Needed for shorter lines
            sim = self.stats[hijack_type][top_nodes_pol][t_obj][adopt_pol][percent_i]
            # Appends a zero onto all stats
            self._initialize_attack_stats(sim)

            self._update_blackholed_disconnected_stats(sim, t_obj, ases_dict)

            ROVPP_Control_Plane_Stats(
                self.args).calculate_not_bholed(self.stats,
                                                sim,
                                                ases_dict, t_obj)

            ROVPP_Data_Plane_Stats(
                self.args).calculate_not_bholed_stats(ases_dict,
                                                      t_obj,
                                                      subp_hijack["attacker"],
                                                      subp_hijack["victim"],
                                                      sim)
            self.logger.debug(sim)
        return (utils.now() - start).total_seconds()

    def _update_blackholed_disconnected_stats(self, sim, t_obj, ases_dict):
        """Updates stats for all ASes that recieved the hijack"""

        # Increase control plane and data plane hijacked
        for plane in Planes.__members__.values():
            for policy in Policies.__members__.values():
                for cond in [Conds.BHOLED.value, Conds.DISCONNECTED.value]:
                    sim[policy.value][plane.value][cond][-1] += ases_dict[t_obj][policy.value][cond]

    def _initialize_attack_stats(self, sim):
        """Defaults the next statistic to be 0 for everything"""

        #I know this could be in a dict comp but ARE YOU NUTS???
        for policy in Policies.__members__.values():
            for plane in Planes.__members__.values():
                for cond in Conds.__members__.values():
                    sim[policy.value][plane.value][cond.value].append(0)

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


    def _get_ases(self, hijack_p, victim_p):

        ases_dict = dict()
        tables = self.tables
        # Get blackholed ases
        # for all blackholed ases, group by subtable
        sqls = ["""DROP TABLE IF EXISTS bholed""",
                """CREATE TABLE bholed AS (
                SELECT exrf.asn FROM
                    rovpp_extrapolation_results_filtered exrf
                INNER JOIN rovpp_blackholes b
                    ON b.asn = exrf.asn);"""]

        for t_obj in tables:
            sqls.extend([
                "DROP TABLE IF EXISTS {0}_bholed;".format(t_obj.table.name),
                 """CREATE TABLE {0}_bholed AS (
                 SELECT b.asn, a.as_type FROM bholed b
                    INNER JOIN {0} a
                 ON a.asn = b.asn);""".format(t_obj.table.name)])
        for sql in sqls:
            self.logger.debug(sql)
            t_obj.table.execute(sql)

        for t_obj in tables:
            sql = """SELECT COUNT(*) FROM {}_bholed b
                  WHERE as_type = """.format(t_obj.table.name)
            ases_dict[t_obj] = dict()
            for pol in Policies.__members__.values():
                tsql = "{} '{}'".format(sql, pol.value)
                ases_dict[t_obj][pol.value] = dict()
                ases_dict[t_obj][pol.value][Conds.BHOLED.value] = \
                    t_obj.table.execute(tsql)[0]["count"]


        # CHANGE THIS TO GET ALL THE SPECIFIC DICTS FOR CTRL AND DATA PLANE FOR EACH POL!!!!!
        # can add all later for iterations
        # NOTE: NOW HAVE SUBTABLES DICT AND AN ALL DICT!!!
        sqls = ["""DROP TABLE IF EXISTS not_bholed""",
                """CREATE TABLE not_bholed AS (
                    SELECT exrf.asn, exrf.received_from_asn,
                            exrf.prefix
                        FROM rovpp_extrapolation_results_filtered exrf
                    LEFT JOIN rovpp_blackholes b
                        ON b.asn = exrf.asn
                    WHERE b.asn IS NULL);"""]
        for cond, pref in zip(['nbh', 'nbnh'], [hijack_p, victim_p]):
            sqls.extend([
                """DROP TABLE IF EXISTS {};""".format(cond),
                """CREATE TABLE {} AS (
                    SELECT nb.asn, nb.received_from_asn
                        FROM not_bholed nb
                    WHERE nb.prefix = '{}');""".format(cond, pref)])

        for t_obj in tables:
            for cond in ['nbh', 'nbnh']:
                sqls.extend([
                    """DROP TABLE IF EXISTS {1}_{0};""".format(t_obj.table.name, cond),
                    """CREATE TABLE {1}_{0} AS (
                           SELECT {1}.asn, {1}.received_from_asn, {0}.as_type
                               FROM {1}
                           INNER JOIN {0}
                               ON {0}.asn = {1}.asn)""".format(t_obj.table.name, cond)])

        for sql in sqls:
            self.logger.debug(sql)
            t_obj.table.execute(sql)


        for t_obj in tables:
            for pol in Policies.__members__.values():
                for cond, tcond in zip(['nbh', 'nbnh'], [Conds.HIJACKED.value, Conds.NOTHIJACKED.value]):
                    sql = """SELECT * FROM {1}_{0}
                          WHERE {1}_{0}.as_type
                          = '{2}'""".format(t_obj.table.name, cond, pol.value)
                    ases_dict[t_obj][pol.value][tcond] = \
                        {x["asn"]: x for x in t_obj.table.execute(sql)}
                sql = """SELECT COUNT(*) FROM ases_with_empty_ribs a
                      INNER JOIN {0} ON {0}.asn = a.asn
                      WHERE {0}.as_type = '{1}'""".format(t_obj.table.name, pol.value)
                ases_dict[t_obj][pol.value][Conds.DISCONNECTED.value] = t_obj.table.execute(sql)[0]["count"]

        ases_dict["nb"] = dict()
        ases_dict[Conds.BHOLED] = dict()
        for t_obj in tables:
            for tcond in Conds.__members__.values():
                for pol in Policies.__members__.values():
                    if tcond.value in [Conds.DISCONNECTED.value, Conds.BHOLED.value]:
                        pass
                    else:
                        ases_dict["nb"].update(ases_dict[t_obj][pol.value][tcond.value])
        return ases_dict
