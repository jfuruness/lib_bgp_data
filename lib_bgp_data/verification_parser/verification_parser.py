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

from .sample_selector import Sample_Selector

from ..asrank_website_parser import ASRankWebsiteParser
from ..base_classes import Parser
from ..database import Database
from ..mrt_parser import MRT_Parser, MRT_Sources
from ..mrt_parser.tables import MRT_Announcements_Table


class Verification_Parser(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def _run(self,
             test=False,
             clear_db=False,
             mrt_announcements=False,
             as_rank=False,
             sample_selection=False,
             ):
        if clear_db and not test:
            assert False, "Clear db, checkpoint, vaccum analyze"
        if mrt_announcements:
            kwargs = {"sources": [MRT_Sources.RIPE, MRT_Sources.ROUTE_VIEWS],
                      "IPV4": True,
                      "IPV6": False}
            if test:
                kwargs["api_param_mods"] = {"collectors[]": ["route-views2",
                                                             "rrc03"]}
            MRT_Parser(**self.kwargs).run(**kwargs)
            # Create index on prefix for sample selection speedup
            with Database() as db:
                sql = f"""CREATE INDEX ON
                       {MRT_Announcements_Table.name}
                       USING GIST(prefix inet_ops)"""
                db.execute(sql)
        if as_rank:
            ASRankWebsiteParser(**self.kwargs).run()
        if sample_selection:
            Sample_Selector().select_samples()
