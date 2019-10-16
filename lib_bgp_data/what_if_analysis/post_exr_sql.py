#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains sql to be run after the extrapolator"""

from .sql_utils import Policies, Validity
from .sql_utils import create_gist, create_index, create_btree
from .sql_utils import create_table_w_gist
from .sql_utils import create_table_w_btree
from .sql_utils import create_table_w_btree_asn

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

def get_post_exr_sql():

    # MUST BE IN EPOCH!!!!!!
    all_sql = []

    return all_sql
