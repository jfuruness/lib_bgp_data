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
from .extrapolator_analyzer import Extrapolator_Analyzer
from .tables import Monitors_Table, Control_Monitors_Table

from ...collectors import AS_Rank_Website_Parser, Relationships_Parser
from ...collectors.mrt import MRT_Parser, MRT_Metadata_Parser, MRT_Sources
from ...collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table
from ...collectors.relationships.tables import Peers_Table
from ...collectors.relationships.tables import Provider_Customers_Table
from ...collectors.roas import ROAs_Parser
from ...utils.base_classes import Parser
from ...utils.database import Database


class Verification_Parser(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def _run(self,
             test=False,
             clear_db=False,
             relationships=True,
             roas=True,
             mrt_announcements=True,
             mrt_metadata=True,
             as_rank=True,
             sample_selection=True,
             dataset_stats=True,
             block_size=2000,
             verification=True,
             ):
        if clear_db and not test:
            assert False, "Clear db, checkpoint, vaccum analyze"
        if relationships:
            Relationships_Parser(**self.kwargs)._run()
        if roas:
            ROAs_Parser(**self.kwargs)._run()
        if mrt_announcements:
            kwargs = {"sources": [MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS]}
            if test:
                kwargs["api_param_mods"] = {"collectors[]": ["route-views2"]}
            MRT_Parser(**self.kwargs)._run(**kwargs)
        if mrt_metadata:
            MRT_Metadata_Parser(**self.kwargs)._run(max_block_size=block_size)
            with MRT_W_Metadata_Table() as db:
                sql = f"""CREATE INDEX monitor_btree
                        ON {db.name}(monitor_asn);"""
                db.execute(sql)
        if as_rank:
            AS_Rank_Website_Parser(**self.kwargs)._run()
        if sample_selection:
            # Fills monitor stats and control table
            for Table in [Monitors_Table, Control_Monitors_Table]:
                with Table(clear=True) as db:
                    db.fill_table()
        if dataset_stats:
            Dataset_Statistics_Generator(**self.kwargs)._run()
        if verification:
            Extrapolator_Analyzer(**self.kwargs)._run(test)
