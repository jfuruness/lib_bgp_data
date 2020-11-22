#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class verification_parser

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
The purpose of this is to generate input from 3 MRT file sources.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .dataset_statistics_generator import Dataset_Statistics_Generator
from .tables import Monitors_Table, Control_Monitors_Table

from ..asrank_website_parser import ASRankWebsiteParser
from ..base_classes import Parser
from ..database import Database
from ..mrt_parser import MRT_Parser, MRT_Metadata_Parser, MRT_Sources
from ..mrt_parser.tables import MRT_W_Metadata_Table
from ..relationships_parser import Relationships_Parser

class Verification_Parser(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def _run(self,
             test=False,
             clear_db=False,
             relationships=False,
             mrt_announcements=False,
             as_rank=False,
             sample_selection=False,
             dataset_stats=False,
             ):
        if clear_db and not test:
            assert False, "Clear db, checkpoint, vaccum analyze"
        if relationships:
            Relationships_Parser(**self.kwargs)._run()
        if mrt_announcements:
            kwargs = {"sources": [MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS],
                      "IPV4": True,
                      "IPV6": False}
            if test:
                kwargs["api_param_mods"] = {"collectors[]": ["route-views2"]}
            MRT_Parser(**self.kwargs)._run(**kwargs)
            MRT_Metadata_Parser(**self.kwargs)._run(**kwargs)
            with MRT_W_Metadata_Table() as db:
                sql = """CREATE INDEX monitor_btree
                        ON {db.name}(monitor_asn);"""
                db.execute(sql)
        if as_rank:
            ASRankWebsiteParser(**self.kwargs)._run()
        if sample_selection:
            # Fills monitor stats and control table
            for Table in [Monitors_Table, Control_Monitors_Table]:
                with Table(clear=True) as db:
                    db.fill_table()
        if dataset_stats:
            Dataset_Statistics_Generator(**self.kwargs)._run()
