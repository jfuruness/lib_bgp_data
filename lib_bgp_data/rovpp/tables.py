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
from .enums import Conditions as Conds
from .enums import Control_Plane_Conditions as C_Plane_Conds
from ..utils import Database, error_catcher, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
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
        if hijack_type != Hijack_Types.NO_COMPETING_ANNOUNCEMENT_HIJACK.value:
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

    def set_implimentable_ases(self, percent, attacker):
        """Sets ases to impliment. Due to large sample size,
           1 (the attacker) is not subtracted from the count,
           since we don't know which data set the attacker is from"""

        sql = """UPDATE {0} SET impliment = TRUE
                FROM (SELECT * FROM {0}
                         WHERE {0}.asn != {1}
                         ORDER BY RANDOM() LIMIT (
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
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_top_100_ases AS (
                 SELECT a.asn, {} AS as_type, FALSE as impliment
                     FROM rovpp_ases a ORDER BY asn DESC LIMIT 100
                 );""".format(Policies.BGP.value)
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
                 );""".format(Policies.BGP.value)
        self.cursor.execute(sql)

class ROVPP_Etc_ASes_Table(ROVPP_ASes_Subtable):
    """Class with database functionality.
    In depth explanation at the top of the file."""

    __slots__ = []

    def fill_table(self, table_names):
        self.clear_table()
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS rovpp_etc_ases AS (
                 SELECT ra.asn, {} AS as_type, FALSE as impliment
                     FROM rovpp_ases ra""".format(Policies.BGP.value)
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
                 opt_hijacked bigint,
                 opt_nothijacked bigint,
                 opt_blackholed bigint,
                 opt_preventivehijacked bigint,
                 opt_preventivenothijacked bigint,
                 opt_total bigint,
                 trace_hijacked bigint,
                 trace_nothijacked bigint,
                 trace_blackholed bigint,
                 trace_preventivehijacked bigint,
                 trace_preventivenothijacked bigint,
                 trace_total bigint,
                 c_plane_has_attacker_prefix_origin bigint,
                 c_plane_has_only_victim_prefix_origin bigint,
                 c_plane_has_bhole bigint,
                 no_rib bigint
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
               opt_flag_data,
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
                 opt_hijacked,
                 opt_nothijacked,
                 opt_blackholed,
                 opt_preventivehijacked,
                 opt_preventivenothijacked,
                 opt_total,
                 trace_hijacked,
                 trace_nothijacked,
                 trace_blackholed,
                 trace_preventivehijacked,
                 trace_preventivenothijacked,
                 trace_total,
                 c_plane_has_attacker_prefix_origin,
                 c_plane_has_only_victim_prefix_origin,
                 c_plane_has_bhole
                 no_rib)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s);"""

        no_rib = c_plane_data[C_Plane_Conds.NO_RIB.value]

        data = [hijack_type,
                subtable_name,
                hijack.attacker_asn,
                hijack.attacker_prefix,
                hijack.victim_asn,
                hijack.victim_prefix,
                adopt_pol_name,
                tnum,
                percent_iter,
                opt_flag_data[Conds.HIJACKED.value],
                opt_flag_data[Conds.NOTHIJACKED.value],
                opt_flag_data[Conds.BHOLED.value],
                opt_flag_data[Conds.PREVENTATIVEHIJACKED.value],
                opt_flag_data[Conds.PREVENTATIVENOTHIJACKED.value],
                sum(v for k, v in opt_flag_data.items()) + no_rib,
                traceback_data[Conds.HIJACKED.value],
                traceback_data[Conds.NOTHIJACKED.value],
                traceback_data[Conds.BHOLED.value],
                traceback_data[Conds.PREVENTATIVEHIJACKED.value],
                traceback_data[Conds.PREVENTATIVENOTHIJACKED.value],
                sum(v for k, v in traceback_data.items()) + no_rib,
                c_plane_data[C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value],
                c_plane_data[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value],
                c_plane_data[C_Plane_Conds.RECEIVED_BHOLE.value],
                no_rib]
        self.cursor.execute(sql, data)

class ROVPP_Statistics_Table(Database):
    """Class with database functionality.

    In depth explanation at the top of the file."""

    __slots__ = ['attacker_asn', 'attacker_prefix', 'victim_asn',
                 'victim_prefix']

    def _create_tables(self):
        """Creates tables if they do not exist.

        Called during initialization of the database class.
        """

        pass

    def clear_table(self):
        """Clears the rovpp_ases table.

        Should be called at the start of every run.
        """

        self.logger.debug("Dropping ROVPP_Statistics_Table")
        self.cursor.execute("DROP TABLE IF EXISTS rovpp_statistics")
        self.logger.debug("ROVPP_All_Statistics_Table Table dropped")

