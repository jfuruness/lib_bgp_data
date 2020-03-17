#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the What_If_Analysis class.

see __init__.py for a deeper explanation
"""

from .pre_exr_sql import get_pre_exr_sql
from .post_exr_sql import get_post_exr_sql
from ..utils import utils, error_catcher, Database, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
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
    def run_pre_exr(self, valid_before_time):
        self.logger.info("Beginning what if analysis for pre processing")
        with db_connection(Database, self.logger) as _db:
            for sql in get_pre_exr_sql(valid_before_time):
                self.logger.info("Executing\n{}".format(sql))
                _db.cursor.execute(sql)

    @error_catcher()
    @utils.run_parser()
    def run_post_exr(self):
        self.logger.info("Beginning what if analysis for post processing")
        with db_connection(Database, self.logger) as _db:
            for sql in get_post_exr_sql():
                self.logger.debug("Executing\n{}".format(sql))
                _db.cursor.execute(sql)
