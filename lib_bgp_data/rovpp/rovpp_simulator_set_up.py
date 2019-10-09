#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
from .enums import Policies, Non_BGP_Policies, Top_Node_Policies, Hijack_Types
from .tables import ROVPP_ASes_Table, Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table
from .tables import ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table
from .rovpp_statistics import ROVPP_Statistics_Calculator
from .graph_data import Graph_Data
from ..relationships_parser import Relationships_Parser
from ..relationships_parser.tables import ROVPP_AS_Connectivity_Table
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..extrapolator import Extrapolator
from ..utils import utils, Database, Config, error_catcher, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# Adding a note here: if take away the possiblity of real data and more than one hijack,
# We can make it so that we can init the mrt announcements, and the ases to impliment
# once per trial, instead of for each policy. This is an optimization

class ROVPP_Simulator_Set_Up_Tool:

    def __init__(self, args):
        utils.set_common_init_args(self, args, paths=False)
        self.args = args

##########################
### Sets up all trials ###
##########################

    @utils.run_parser(paths=False)
    def set_up_all_trials_and_percents(self):
        self._get_relationship_data()
        self._create_and_fill_as_and_connectivity_tables()

    def _get_relationship_data(self):
        """Gets relationship data, small func ik but makes code cleaner"""

        self.logger.debug("Getting relationship data for rovpp simulator")

        # Runs relationships parser
        caida_url = "http://data.caida.org/datasets/as-relationships/serial-2/"
        may_data_url = caida_url + "20190501.as-rel2.txt.bz2"
        DEBUG = 10  # cannot import logger because not threadsafe
        WARNING = 30
        args = deepcopy(self.args)
        if self.args["stream_level"] == DEBUG:
            args["sream_level"] = DEBUG
        else:
            args["stream_level"] = WARNING
        Relationships_Parser(args).parse_files(rovpp=True, url=may_data_url)

        self.logger.debug("Done getting relationship data for rovpp simulator")


    def _create_and_fill_as_and_connectivity_tables(self):
        with db_connection(ROVPP_ASes_Table, self.logger) as as_table:
            as_table.fill_table()
        with db_connection(ROVPP_AS_Connectivity_Table,
                           self.logger) as connectivity_table:
            pass

#############################
### Sets Up Current Trial ###
#############################

    def set_up_trial(self, percents, iter_num, top_nodes_pol, hijack_type):
        # Creates fresh subtables, faster than reverting back to bgp
        self._create_subtables(percents, top_nodes_pol)

        hijack = self._get_hijack_data(hijack_type)
        
        self._set_implimentable_ases(iter_num, hijack["attacker"])

        self._populate_rovpp_mrt_announcements(hijack, hijack_type)

        return self.tables, hijack


    def _create_subtables(self, default_percents, top_nodes_pol):
        # Add docs on how to add a table to these sims
        # Create these tables and then 
        # Create an everything else table
        self.tables = [Subtable(ROVPP_Top_100_ASes_Table,
                                self.logger,
                                [25]*len(default_percents),
                                possible_hijacker=False,
                                policy_to_impliment=top_nodes_pol),
                       Subtable(ROVPP_Edge_ASes_Table,
                                self.logger,
                                default_percents)]
        for sub_table in self.tables:
            sub_table.table.fill_table()

        etc = Subtable(ROVPP_Etc_ASes_Table, self.logger, default_percents)
        etc.table.fill_table([x.table.name for x in self.tables])
        self.tables.append(etc)

    def _get_hijack_data(self, hijack_type):
        """Gets bgpstream data, small fun ik but makes code cleaner"""

        self.logger.debug("Creating fake data for subprefix hijacks")
        # Initializes the fake table
        with db_connection(Subprefix_Hijack_Temp_Table, self.logger) as db:
            db.populate(self._get_possible_hijacker_ases(), hijack_type)
            # Returns all the subprefix hijacks - should only be one
            return db.get_all()[0]

    def _get_possible_hijacker_ases(self):
        """Returns all possible hijacker ases"""

        possible_hijacker_ases = []
        for _table in self.tables:
            if _table.possible_hijacker:
                results = _table.table.get_all()
                possible_hijacker_ases.extend([x["asn"] for x in results])
        return possible_hijacker_ases

    def _set_implimentable_ases(self, percent_iteration_num, attacker):

        for sub_table in self.tables:
            sub_table.set_implimentable_ases(percent_iteration_num, attacker)

    def _populate_rovpp_mrt_announcements(self, subprefix_hijack, hijack_type):
        """Fill the rovpp mrt announcements table"""

        self.logger.debug("Populating rovpp announcements table")
        # I know this is a short function but it's for readability
        with db_connection(ROVPP_MRT_Announcements_Table,
                           self.logger) as mrt_table:
            mrt_table.populate_mrt_announcements(subprefix_hijack, hijack_type)
        self.logger.debug("Done populating rovpp announcements table")


class Subtable:
    """Subtable class for ease of use"""

    def __init__(self,
                 table,
                 logger,
                 percents,
                 possible_hijacker=True,
                 policy_to_impliment=None):
        self.logger = logger
        self.table = table(logger)
        self.count = self.table.get_count()
        self.percents = percents
        self.possible_hijacker = possible_hijacker
        # None for whatever policy is being tested
        self.policy_to_impliment = policy_to_impliment

    def set_implimentable_ases(self, iteration_num, attacker):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)
