#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator

The purpose of this class is to run the extrapolator.
For more info see: https://github.com/c-morris/BGPExtrapolator
For the specifics on how the extrapolator is run see each function
"""

from subprocess import check_call, DEVNULL
from .tables import Extrapolator_Inverse_Results_Table
from ..utils import error_catcher, utils, db_connection
# Justin globals are bad yah you know what else is bad? the logging
# module that deadlocks upon import
DEBUG = 10

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Extrapolator:
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = ['path', 'csv_dir', 'logger']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)

    @error_catcher()
    @utils.run_parser()
    def run_forecast(self, input_table=None, extraprefix=False):
        self.logger.info("About to run the forecast extrapolator")
        bash_args = "forecast-extrapolator"
        if input_table:
            bash_args += " -a {}".format(input_table)
        if superprefix:
            o_table = "extrapolation_inverse_results_extraprefixes"
            bash_args += " -o {}".format(o_table)
        if self.logger.level == DEBUG:
            check_call(bash_args, shell=True)
        else:
            check_call(bash_args, stdout=DEVNULL, stderr=DEVNULL, shell=True)
        self._create_index()

    @error_catcher()
    def _create_index(self):
        self.logger.info("Creating index on the extrapolation results")
        with db_connection(Extrapolator_Inverse_Results_Table,
                           self.logger) as db:
            db.create_index()

    @error_catcher()
    @utils.run_parser()
    def run_rovpp(self, hijack, table_names):
        """Runs extrapolator with a subprefix hijack."""

        self.logger.debug("About to run the rovpp extrapolator")
        # Run the extrapolator
        bash_args = "rovpp-extrapolator "
        # Don't invert the results so that we have the last hop
        bash_args += "--invert-results=0 "
        # Gives the attacker asn
        bash_args += "--attacker_asn={} ".format(hijack.attacker)
        # Gives the victim asn
        bash_args += "--victim_asn={} ".format(hijack.victim)
        # Gives the more specific prefix that the attacker sent out
        bash_args += "--victim_prefix={} ".format(hijack.victim_prefix)
        bash_args += "--rovpp_ases_tables {}".format(" ".join(table_names))
        self.logger.debug("Caling extrapolator with:\n{}".format(bash_args))
        if self.logger.level == DEBUG:
            check_call(bash_args, shell=True)
        else:
            check_call(bash_args, stdout=DEVNULL, stderr=DEVNULL, shell=True)
        self._filter_extrapolator(hijack)
        self._join_w_tables(table_names)

    def _filter_extrapolator(self, hijack):
        with db_connection() as db:
            db.execute("DROP TABLE IF EXISTS rovpp_extrapolation_results_filtered")

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

            db.execute(sql, [hijack.attacker_prefix, hijack.victim_prefix])

    def _join_w_tables(self, table_names):
        with db_connection() as db:
            for table_name in table_names:
                sql = "DROP TABLE IF EXISTS rovpp_exr_{}".format(table_name)
                db.execute(sql)
                sql = """CREATE TABLE rovpp_exr_{} AS (
                      SELECT exr.asn, exr.prefix, exr.origin, {0}.as_type
                          FROM rovpp_extrapolation_results_filtered exr
                      INNER JOIN {0} ON
                          {0}.asn = exr.asn);""".format(table_name)
                db.execute(sql) 
