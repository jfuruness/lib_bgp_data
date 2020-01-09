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
    def run_forecast(self, input_table):
        self.logger.info("About to run the forecast extrapolator")

        bash_args = "forecast-extrapolator"
        bash_args += " -a {}".format(input_table)

        bash_args += " -r exr_results -d exr_results_depref"

        if self.logger.level == DEBUG:
            check_call(bash_args, shell=True)
        else:
            check_call(bash_args, stdout=DEVNULL, stderr=DEVNULL, shell=True)


    @error_catcher()
    @utils.run_parser()
    def run_rovpp(self, hijack, table_names, exr_bash=None, test=False):
        """Runs extrapolator with a subprefix hijack."""

        self.logger.debug("About to run the rovpp extrapolator")
        # Run the extrapolator
        bash_args = "rovpp-extrapolator "
        # version 1
        bash_args += "-v 1 "
        # lists tables nessecary
        for table_name in table_names:
            bash_args += "-t {}".format(table_name)
        if test is True:
            bash_args = ("rovpp-extrapolator -v 1 "
                         "-t rovpp_top_100_ases "
                         "-t rovpp_etc_ases "
                         "-t rovpp_edge_ases "
                         "-b 0 "  # deterministic
                         "-k 1")  # double propogation
        if exr_bash is not None:
            bash_args = exr_bash
        self._call_exr(bash_args)
        self._filter_extrapolator(hijack)
        self._join_w_tables(table_names)

        # For testing single vs double prop
        if test is True:
            bash_args = bash_args[:-1] + "0 -r rovpp_exr_single_prop_test"
            self._call_exr(bash_args)
            with db_connection(logger=self.logger) as db:
                db.execute("ALTER TABLE rovpp_exr_single_prop_test ADD COLUMN alternate_as bigint;")

                assert len(db.execute("SELECT * FROM rovpp_extrapolation_results EXCEPT SELECT * FROM rovpp_exr_single_prop_test")) == 0
                assert len(db.execute("SELECT * FROM rovpp_exr_single_prop_test EXCEPT SELECT * FROM rovpp_extrapolation_results")) == 0


    def _call_exr(self, bash_args):
        self.logger.debug("Calling extrapolator with:\n\t{}".format(bash_args))
        if self.logger.level == DEBUG:
            check_call(bash_args, shell=True)
        else:
            check_call(bash_args, stdout=open('/tmp/extrapolatordebug.log','w'), stderr=DEVNULL, shell=True)


    def _filter_extrapolator(self, hijack):
        with db_connection() as db:
            db.execute("ALTER TABLE rovpp_extrapolation_results ADD COLUMN alternate_as bigint;")
            db.execute("DROP TABLE IF EXISTS rovpp_extrapolation_results_filtered")
            sql = """CREATE TABLE rovpp_extrapolation_results_filtered AS (
                  SELECT DISTINCT ON (exr.asn) exr.asn, exr.opt_flag, exr.alternate_as,
                         COALESCE(exrh.prefix, exrnh.prefix) AS prefix,
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
                sql = """CREATE TABLE rovpp_exr_{0} AS (
                      SELECT exr.asn, exr.opt_flag, exr.prefix, exr.origin, exr.alternate_as,
                              exr.received_from_asn, {0}.as_type
                          FROM rovpp_extrapolation_results_filtered exr
                      INNER JOIN {0} ON
                          {0}.asn = exr.asn);""".format(table_name)
                db.execute(sql) 
