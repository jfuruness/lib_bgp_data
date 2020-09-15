#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This package contains all parsers neccessary to parse bgp data

This is also where the logging is taken care of. That is because this
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os

from .relationships_parser import Relationships_Parser
from .roas_parser import ROAs_Parser, ROAs_Collector
from .bgpstream_website_parser import BGPStream_Website_Runner
from .bgpstream_website_parser import BGPStream_Website_Parser
from .bgpstream_website_parser import Event_Types as BGPStream_Types
from .mrt_parser import MRT_Parser, MRT_Sources
from .asrank_website_parser import ASRankWebsiteParser

#from .what_if_analysis import What_If_Analysis
from .rpki_validator import RPKI_Validator_Wrapper, RPKI_Validator_Parser
#from .api import create_app
from .extrapolator_parser import Extrapolator_Parser
from .database import Database, Postgres, Generic_Table
from .rovpp import ROVPP_Simulator, Simulation_Grapher
#from .forecast import Forecast
from .cdn_whitelist import CDN_Whitelist
from .blacklist_parser import Blacklist_Parser

class NotSudo(Exception):
    pass

if os.getuid() != 0:
    raise NotSudo("Sudo priveleges are required")
