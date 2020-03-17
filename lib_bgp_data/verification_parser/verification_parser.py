#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class verification_parser

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
The purpose of this is to generate input from 3 MRT file sources.
"""

from ..mrt_parser import MRT_Parser, MRT_Sources
from ..utils import error_catcher, utils, db_connection
DEBUG = 10

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class Verification_Parser:
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'args']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        self.args = args

#    @error_catcher()
#    @utils.run_parser()
    def parse_files(self, start=1573430400, end=1573516800):
        self.logger.info("About to download the Caida data")
        start = 1573430400
        end = 1573516800
        for mrt_source in [x.value for x in MRT_Sources.__members__.values()]:
            MRT_Parser(self.args).parse_files(start, end, sources=[mrt_source])
            with db_connection(logger=self.logger) as db:
                db.execute("DROP TABLE IF EXISTS {}".format(mrt_source))
                db.execute("""ALTER TABLE mrt_announcements
                           RENAME TO {}""".format(mrt_source))
