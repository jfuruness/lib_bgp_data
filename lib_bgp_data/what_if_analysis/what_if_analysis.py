#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the What_If_Analysis class.

see __init__.py for a deeper explanation
"""

from .split_validity_sql import split_validity_table_sql
from .sql_queries import all_sql_queries
from ..utils import utils, error_catcher, Database, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class What_If_Analysis:
    """This class runs all the security policies."""

    __slots__ = ['path', 'csv_dir', 'logger']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args)

    @error_catcher()
    @utils.run_parser()
    def run_rov_policy(self):
        self.logger.info("Beginning what if analysis")
        with db_connection(Database, self.logger) as _db:
            for sql in split_validity_table_sql + all_sql_queries:
                self.logger.debug("Executing\n{}".format(sql))
                _db.cursor.execute(sql)
