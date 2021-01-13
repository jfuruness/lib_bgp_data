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

# Collectors
from .collectors import AS_Rank_Website_Parser
from .collectors import BGPStream_Website_Parser
from .collectors.bgpstream_website import BGPStream_Website_Event_Types as BGPStream_Types
from .collectors import Blacklist_Parser
from .collectors import CDN_Whitelist_Parser
from .collectors import Historical_ROAs_Parser
from .collectors.mrt import MRT_Parser, MRT_Metadata_Parser, MRT_Sources
from .collectors import MRT_Metadata_Parser
from .collectors import Relationships_Parser
from .collectors import ROAs_Parser
from .collectors import RPKI_Validator_Parser, RPKI_Validator_Wrapper
# Extrapolator
from .extrapolator import Verification_Parser
from .extrapolator import EZ_BGP_Extrapolator_Wrapper
# enum for adopt policies
from .simulations import Non_Default_Policies
# Simulator attacks
from .simulations import Attack
from .simulations import Subprefix_Hijack
from .simulations import Prefix_Hijack
from .simulations import Prefix_Superprefix_Hijack
from .simulations import Unannounced_Prefix_Hijack
from .simulations import Unannounced_Subprefix_Hijack
from .simulations import Unannounced_Prefix_Superprefix_Hijack

from .simulations import Naive_Origin_Hijack
from .simulations import Intermediate_AS_Hijack_1
from .simulations import Intermediate_AS_Hijack_2
from .simulations import Intermediate_AS_Hijack_3
from .simulations import Intermediate_AS_Hijack_4
from .simulations import Intermediate_AS_Hijack_5

# Actual simulations
from .simulations import Simulator, Simulation_Grapher

from .utils.database import Database, Postgres, Generic_Table
"""
from .database import Database, Postgres, Generic_Table
from .rovpp import ROVPP_Simulator, Simulation_Grapher
from .verification_parser import Verification_Parser
"""

class NotSudo(Exception):
    pass

if os.getuid() != 0:
    raise NotSudo("Sudo priveleges are required")
