#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class BGPStream_DB

BGPStream_DB has database functionality for bgpstream events
It inherits functions from Hijack_DB, Leak_DB, and Outage_DB to
interact with the database
"""

from .leak_db import Leak_DB
from .hijack_db import Hijack_DB
from .outage_db import Outage_DB
from .bgpstream_database_wrapper import BGPStream_DB_Wrapper


class BGPStream_DB(Leak_DB, Hijack_DB, Outage_DB, BGPStream_DB_Wrapper):
    """Interacts with database to add bgpstream data
    
    contains functions from leak hijack outage and wrapper db classes
    """

    def __init__(self, verbose):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """
        pass

