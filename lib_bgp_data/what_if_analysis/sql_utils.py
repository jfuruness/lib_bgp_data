#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains utils for sql"""

from enum import Enum

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Policies(Enum):
    ASN = "asn"
    LENGTH = "length"
    ROV = "rov"

class Validity(Enum):
    VALID = "valid"
    INVALID = "invalid"


#############################################################
### To be run post mrt_parse to get input to extrapolator ###
#############################################################

def create_gist(table_name, extra=False):
    prefix = "extra_prefix" if extra else "prefix"
    origin = "extra_origin" if extra else "origin"

    return """CREATE INDEX ON {}
           USING GIST({} inet_ops, {});""".format(table_name, prefix, origin)

def create_index(table_name, indexed_column):
    return "CREATE INDEX ON {}({});".format(table_name, indexed_column)

def create_btree(table_name, extra=False, asn=False):
    indexed_column = "extra_mrt_index" if extra else "mrt_index"
    indexed_column = "asn" if asn else indexed_column
    return create_index(table_name, indexed_column)

def create_table_w_index(table_name, select_sql, index_func, extra=False):
    create_table_sql = "CREATE UNLOGGED TABLE IF NOT EXISTS {} AS (".format(
        table_name)
    create_table_sql += select_sql + ");"

    sql = ["DROP TABLE IF EXISTS {}".format(table_name),
            create_table_sql,
            index_func(table_name)]
    if extra:
        sql.append(index_func(table_name, extra=True))
    return sql

def create_table_w_gist(t_name, select_sql, extra=False):
    return create_table_w_index(t_name, select_sql, create_gist, extra)

def create_table_w_btree(t_name, select_sql, extra=False):
    return create_table_w_index(t_name, select_sql, create_btree, extra)

def create_table_w_btree_asn(t_name, select_sql, extra=False):
    return create_table_w_index(t_name, select_sql, create_btree, extra, asn=True)

