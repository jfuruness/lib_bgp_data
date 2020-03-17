#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains ROVPP_ASes_Table and Subprefix_Hijack_Temp_Table

These two classes inherits from the Database class. The Database class
does allow for the conection to a database upon initialization. Also
upon initialization the _create_tables function is called to initialize
any tables if they do not yet exist. Beyond that the class can clear the
table, create an index, and has the name and columns properties that are
used in utils function to insert CSVs into the database. This class does
not contain an index creation function, because it would only ever be
used when combining with the roas table, which does a parallel seq_scan,
thus any indexes are not used since they are not efficient. Each table
follows the table name followed by a _Table since it inherits from the
database class.

Possible future improvements:
    -Add test cases
"""

from random import sample
from .enums import Policies, Hijack_Types
from .enums import AS_Types, Conditions as Conds
from .enums import Control_Plane_Conditions as C_Plane_Conds
from ..database import Database

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class ROVPP_MRT_Announcements_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
                 rovpp_mrt_announcements (
                 origin bigint,
                 as_path bigint ARRAY,
                 prefix CIDR,
                 attacker BOOLEAN
                 );"""
        self.cursor.execute(sql)

        

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping ROVPP_MRT_Announcements")
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_mrt_announcements")
        self.logger.debug("ROVPP_MRT_Announcements Table dropped")

    def populate_mrt_announcements(self, subprefix_hijack, hijack_type):
        """Populates the mrt announcements table"""

        sql = """INSERT INTO rovpp_mrt_announcements(
              origin, as_path, prefix, attacker) VALUES
              (%s, %s, %s, %s)"""
        attacker_data = [subprefix_hijack.attacker_asn,
                         [subprefix_hijack.attacker_asn],
                         subprefix_hijack.attacker_prefix,
                         True]
        victim_data = [subprefix_hijack.victim_asn,
                       [subprefix_hijack.victim_asn],
                       subprefix_hijack.victim_prefix,
                       False]
        data_list = [attacker_data]
        if hijack_type != Hijack_Types.UNANNOUNCED_PREFIX_HIJACK.value:
            data_list.append(victim_data)
        for data in data_list:
            self.cursor.execute(sql, data)

        # Split into two separate tables, because we decided to use a bool
        # and other people keep going back and forth so gonna leave it
        sql = """CREATE TABLE {} AS
              SELECT origin, as_path, prefix FROM rovpp_mrt_announcements
              WHERE attacker = {}"""
        for attacker, table in zip([True, False], ["attackers", "victims"]):
            self.cursor.execute("DROP TABLE IF EXISTS " + table)
            self.cursor.execute(sql.format(table, attacker))

class Subprefix_Hijack_Temp_Table(Database):
    """Class with database functionality.

    THIS SHOULD BE DELETED LATER AND ADDED INTO BGPSTREAM.COM CLASS!!!
    THIS IS JUST FOR FAKE DATA!!!!

    In depth explanation at the top of the file."""

    __slots__ = []

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        self.clear_table()
        sql = """CREATE UNLOGGED TABLE subprefix_hijack_temp(
                 more_specific_prefix CIDR,
                 attacker bigint,
                 url varchar(200),
                 expected_prefix CIDR,
                 victim bigint
                 );"""
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping Subprefix Hijacks")
        self.cursor.execute("DROP TABLE IF EXISTS subprefix_hijack_temp;")
        self.logger.debug("Subprefix Hijacks Table dropped")

    def populate(self, ases, hijack_type):
        """Populates table with fake data"""

        # Gets two random ases without duplicates
        attacker, victim = sample(ases, k=2)
        sql = """INSERT INTO subprefix_hijack_temp(
              more_specific_prefix, attacker, expected_prefix, victim) VALUES
              (%s, %s, %s, %s)"""
        data = ['1.2.3.0/24',  # more_specfic_prefix
                attacker,  # Random attacker
                '1.2.0.0/16',  # expected_prefix
                victim]
        if hijack_type == Hijack_Types.PREFIX_HIJACK.value:
            data[0] = data[2]
        self.cursor.execute(sql, data)

        self.logger.debug("Creating fake data for subprefix hijacks")
        hijack = Hijack(self.get_all()[0])
        with db_connection(ROVPP_MRT_Announcements_Table) as db:
            db.populate_mrt_announcements(hijack, hijack_type)
        return hijack

class Hijack:
    def __init__(self, info_dict):
        self.attacker_asn = info_dict.get("attacker")
        self.attacker_prefix = info_dict.get("more_specific_prefix")
        self.victim_asn = info_dict.get("victim")
        self.victim_prefix = info_dict.get("expected_prefix")

    def __repr__(self):
        my_str = (f"Attacker: {self.attacker_asn:<8}, prefix: {self.attacker_prefix}\n"
                  f"Victim:   {self.victim_asn:<8}, prefix: {self.victim_prefix}\n")
        

####################
### Subtables!!! ###
####################

class ROVPP_ASes_Subtable(Database):
    def _create_tables(self):
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS {} (
                 asn bigint,
                 as_type text,
                 impliment BOOLEAN
                 );""".format(self.name)
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.
        Should be called at the start of every run.
        """

        self.logger.debug("Dropping {}".format(self.name))
        self.cursor.execute("DROP TABLE IF EXISTS {}".format(self.name))
        self.logger.debug("{} dropped".format(self.name))

    def set_implimentable_ases(self, percent, attacker, deterministic):
        """Sets ases to impliment. Due to large sample size,
           1 (the attacker) is not subtracted from the count,
           since we don't know which data set the attacker is from"""

        if deterministic:
            ases = sorted(set([x["asn"] for x
                               in self.execute("SELECT * FROM " + self.name)]))
            ases.remove(attacker)
            num_ases = len(ases) * percent // 100
            impliment_ases = sample(ases, k=num_ases)
            for _as in impliment_ases:
                self.execute("""UPDATE {} SET impliment = TRUE
                                WHERE asn = {}""".format(self.name, _as))
        else:

            sql = """UPDATE {0} SET impliment = TRUE
                    FROM (SELECT * FROM {0}
                             WHERE {0}.asn != {1}
                             ORDER BY RANDOM() LIBSD (
                                 SELECT COUNT(*) FROM {0}) * ({2}::decimal/100.0)
                             ) b
                   WHERE b.asn = {0}.asn;""".format(self.name, attacker, percent)
            self.execute(sql)

    def change_routing_policies(self, policy):
        sql = """UPDATE {} SET as_type = {}
                 WHERE impliment = TRUE;""".format(self.name, policy)
        self.execute(sql)


class ROVPP_Top_100_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self):
        self.clear_table()
        # TODO deadlines so fuck it
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_top_100_ases AS (
                 SELECT a.asn, {} AS as_type, FALSE as impliment
                     FROM rovpp_ases a WHERE asn = 3356
                     OR asn = 1299
OR asn = 174
OR asn = 2914
OR asn = 3257
OR asn = 6762
OR asn = 6939
OR asn = 6453
OR asn = 3491
OR asn = 6461
OR asn = 1273
OR asn = 3549
OR asn = 9002
OR asn = 5511
OR asn = 12956
OR asn = 4637
OR asn = 7473
OR asn = 209
OR asn = 12389
OR asn = 701
OR asn = 3320
OR asn = 7018
OR asn = 7922
OR asn = 20485
OR asn = 3216
OR asn = 9498
OR asn = 31133
OR asn = 20764
OR asn = 6830
OR asn = 1239
OR asn = 52320
OR asn = 16735
OR asn = 2828
OR asn = 15412
OR asn = 8359
OR asn = 286
OR asn = 58453
OR asn = 28917
OR asn = 262589
OR asn = 10429
OR asn = 4809
OR asn = 7738
OR asn = 4755
OR asn = 41095
OR asn = 37468
OR asn = 33891
OR asn = 43531
OR asn = 4766
OR asn = 11537
OR asn = 8220
OR asn = 31500
OR asn = 4826
OR asn = 18881
OR asn = 7843
OR asn = 29076
OR asn = 4230
OR asn = 46887
OR asn = 34800
OR asn = 62663
OR asn = 8167
OR asn = 9304
OR asn = 7029
OR asn = 5588
OR asn = 267613
OR asn = 3303
OR asn = 11164
OR asn = 20804
OR asn = 8218
OR asn = 5617
OR asn = 4134
OR asn = 1221
OR asn = 7474
OR asn = 13786
OR asn = 22773
OR asn = 9049
OR asn = 28329
OR asn = 12741
OR asn = 61832
OR asn = 28598
OR asn = 132602
OR asn = 3326
OR asn = 22356
OR asn = 2516
OR asn = 7545
OR asn = 26615
OR asn = 6663
OR asn = 2497
OR asn = 577
OR asn = 23520
OR asn = 55410
OR asn = 9318
OR asn = 3786
OR asn = 20115
OR asn = 3267
OR asn = 3223
OR asn = 20562
OR asn = 6128
OR asn = 3741
OR asn = 9505
OR asn = 50607

                 );""".format(Policies.DEFAULT.value)              
        self.cursor.execute(sql)


class ROVPP_Edge_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self):
        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_edge_ases AS (
                     SELECT r.asn, {} AS as_type, FALSE as impliment
                         FROM rovpp_ases r
                         INNER JOIN rovpp_as_connectivity c ON c.asn = r.asn
                     WHERE c.connectivity = 0
                 );""".format(Policies.DEFAULT.value)
        self.cursor.execute(sql)

class ROVPP_Etc_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self, table_names):
        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_etc_ases AS (
                 SELECT ra.asn, {} AS as_type, FALSE as impliment
                     FROM rovpp_ases ra""".format(Policies.DEFAULT.value)
        if len(table_names) > 0:
            for table_name in table_names:
                sql += " LEFT JOIN {0} ON {0}.asn = ra.asn".format(table_name)
            # Gets rid of the last comma
            sql += " WHERE"
            for table_name in table_names:
                sql += " {}.asn IS NULL AND".format(table_name)
            # Gets rid of the last \sAND
            sql = sql[:-4]
        sql += ");"
        self.logger.debug("ETC AS SQL:\n\n{}\n".format(sql))
        self.cursor.execute(sql)

class ROVPP_All_Trials_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS
                 rovpp_all_trials (
                 hijack_type varchar(50),
                 subtable_name varchar(50),
                 attacker_asn bigint,
                 attacker_prefix CIDR,
                 victim bigint,
                 victim_prefix CIDR,
                 adopt_pol varchar(50),
                 trial_num bigint,
                 percent_iter bigint,
                 trace_hijacked_collateral bigint,
                 trace_nothijacked_collateral bigint,
                 trace_blackholed_collateral bigint,
                 trace_preventivehijacked_collateral bigint,
                 trace_preventivenothijacked_collateral bigint,
                 trace_total_collateral bigint,
                 trace_hijacked_adopting bigint,
                 trace_nothijacked_adopting bigint,
                 trace_blackholed_adopting bigint,
                 trace_preventivehijacked_adopting bigint,
                 trace_preventivenothijacked_adopting bigint,
                 trace_total_adopting bigint,
                 c_plane_has_attacker_prefix_origin_collateral bigint,
                 c_plane_has_only_victim_prefix_origin_collateral bigint,
                 c_plane_has_bhole_collateral bigint,
                 no_rib_collateral bigint,
                 c_plane_has_attacker_prefix_origin_adopting bigint,
                 c_plane_has_only_victim_prefix_origin_adopting bigint,
                 c_plane_has_bhole_adopting bigint,
                 no_rib_adopting bigint
                 );"""
        self.cursor.execute(sql)

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping ROVPP_All_Trials_Table")
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_all_trials")
        self.logger.debug("ROVPP_All_Trials_Table Table dropped")

    def insert(self,
               subtable_name,
               hijack,
               hijack_type,
               adopt_pol_name,
               tnum,
               percent_iter,
               traceback_data,
               c_plane_data):

        sql = """INSERT INTO rovpp_all_trials(
                 hijack_type,
                 subtable_name,
                 attacker_asn,
                 attacker_prefix,
                 victim,
                 victim_prefix,
                 adopt_pol,
                 trial_num,
                 percent_iter,
                 trace_hijacked_collateral,
                 trace_nothijacked_collateral,
                 trace_blackholed_collateral,
                 trace_preventivehijacked_collateral,
                 trace_preventivenothijacked_collateral,
                 trace_total_collateral,
                 trace_hijacked_adopting,
                 trace_nothijacked_adopting,
                 trace_blackholed_adopting,
                 trace_preventivehijacked_adopting,
                 trace_preventivenothijacked_adopting,
                 trace_total_adopting,
                 c_plane_has_attacker_prefix_origin_collateral,
                 c_plane_has_only_victim_prefix_origin_collateral,
                 c_plane_has_bhole_collateral,
                 no_rib_collateral,
                 c_plane_has_attacker_prefix_origin_adopting,
                 c_plane_has_only_victim_prefix_origin_adopting,
                 c_plane_has_bhole_adopting,
                 no_rib_adopting)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

        data = [hijack_type,
                subtable_name,
                hijack.attacker_asn,
                hijack.attacker_prefix,
                hijack.victim_asn,
                hijack.victim_prefix,
                adopt_pol_name,
                tnum,
                percent_iter,

                traceback_data[Conds.HIJACKED.value][AS_Types.NON_ADOPTING.value],
                traceback_data[Conds.NOTHIJACKED.value][AS_Types.NON_ADOPTING.value],
                traceback_data[Conds.BHOLED.value][AS_Types.NON_ADOPTING.value],
                traceback_data[Conds.PREVENTATIVEHIJACKED.value][AS_Types.NON_ADOPTING.value],
                traceback_data[Conds.PREVENTATIVENOTHIJACKED.value][AS_Types.NON_ADOPTING.value],
                int(sum(v[AS_Types.NON_ADOPTING.value] for k, v in traceback_data.items())) + c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.NO_RIB.value],

                traceback_data[Conds.HIJACKED.value][AS_Types.ADOPTING.value],
                traceback_data[Conds.NOTHIJACKED.value][AS_Types.ADOPTING.value],
                traceback_data[Conds.BHOLED.value][AS_Types.ADOPTING.value],
                traceback_data[Conds.PREVENTATIVEHIJACKED.value][AS_Types.ADOPTING.value],
                traceback_data[Conds.PREVENTATIVENOTHIJACKED.value][AS_Types.ADOPTING.value],
                int(sum(v[AS_Types.ADOPTING.value] for k, v in traceback_data.items())) + c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.NO_RIB.value],

                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.RECEIVED_BHOLE.value],
                c_plane_data[AS_Types.NON_ADOPTING.value][C_Plane_Conds.NO_RIB.value],

                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.RECEIVED_BHOLE.value],
                c_plane_data[AS_Types.ADOPTING.value][C_Plane_Conds.NO_RIB.value]]
        self.cursor.execute(sql, data)
