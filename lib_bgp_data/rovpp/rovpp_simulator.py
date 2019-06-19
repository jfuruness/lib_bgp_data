#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class ROVPP_Simulator

The purpose of this class is to run simulations for the ROVPP project.
For further details on the ROVPP project please see the paper listed
<PROVIDE URL HERE!!!!!!!!!!>
For the steps on how the rovpp parser is run, see below:

1. The relationships parser is run
    -Handled in the simulate function
    -A static url (below) is used so that the topology doesn't change
    -http://data.caida.org/datasets/as-relationships/
     serial-2/20190501.as-rel2.txt.bz2
    -rovpp simulation args are passed in so that data is stored within
     rovpp_customer_providers and rovpp_peers
2.

Design choices (summarizing from above):

Possible Future Extensions:
    -Add test cases
"""

from random import sample
from subprocess import check_call
from copy import deepcopy
from .enums import Policies, Non_BGP_Policies
from .tables import ROVPP_ASes_Table, Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table
from .rovpp_statistics import ROVPP_Statistics_Calculator
from ..relationships_parser import Relationships_Parser
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..extrapolator import Extrapolator
from ..utils import utils, Database, Config, error_catcher, db_connection

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


class ROVPP_Simulator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'statistics_calculator']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        # Define statistics calculator - also where stats are stored
        self.statistics_calculator = ROVPP_Statistics_Calculator()

    @error_catcher()
    @utils.run_parser()
    def simulate(self, real_data=False):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Runs relationships_parser
        self.logger.info("Getting relationship data for rovpp simulator")
        self._get_relationship_data()
        self.logger.debug("Done getting relationship data for rovpp simulator")
                
        # Populates table
        self.logger.info("Initializing rovpp_as_table")
        with db_connection(ROVPP_ASes_Table, self.logger) as as_table:
            # Gets all ASes within the topology
            ases = [x["asn"] for x in as_table.get_all()]
            # Gets hijack data
            self._get_hijack_data(real_data, ases)

            # Could be done in list comp but this is more readable
            # We use non bgp policies because bgp is the default
            for policy in Non_BGP_Policies.__members__.values():
                if policy.value == 'rovpp':#########################
                    continue
                # For every percent
                for percent in range(101):
                    # Run that specific simulation
                    self._run_simulation(policy.value, percent, ases, as_table)

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_relationship_data(self):
        """Gets relationship data, small func ik but makes code cleaner"""

        # Runs relationships parser
        caida_url = "http://data.caida.org/datasets/as-relationships/serial-2/"
        may_data_url = caida_url + "20190501.as-rel2.txt.bz2"
        Relationships_Parser.parse_files(self, rovpp=True, url=may_data_url)

    @error_catcher()
    def _get_hijack_data(self, real_data=False, ases=[]):
        """Gets bgpstream data, small fun ik but makes code cleaner"""

        if real_data:
            self.logger.info("Getting real data from bgpstream.com")
            # Runs the bgpstream_website parser        
            BGPStream_Website_Parser().parse(start='2019-05-07 00:00:00',
                                             end='2019-05-07 00:00:00')
            self.logger.debug("Done getting data from bgpstream.com")
        else:
            self.logger.info("Creating fake data for subprefix hijacks")
            # Initializes the fake table
            with db_connection(Subprefix_Hijack_Temp_Table,
                               self.logger) as fake_table:
                fake_table.populate(ases)
            self.logger.debug("Done creating fake data for subprefix hijacks")

    @error_catcher()
    def _run_simulation(self, policy, percentage, ases, as_table):
        """Runs one single simulation with the extrapolator"""

        self.logger.info("Running policy: {} percent {}".format(percentage,
            policy))
        self._change_routing_policy(percentage, ases, as_table, policy)
        subprefix_hijacks = as_table.execute("SELECT * FROM subprefix_hijack_temp")
        for i, subprefix_hijack in enumerate(subprefix_hijacks):
            self._populate_rovpp_mrt_announcements(subprefix_hijack)
            Extrapolator().run_rovpp(subprefix_hijack["attacker"],
                                     subprefix_hijack["victim"],
                                     subprefix_hijack["expected_prefix"])
            self.statistics_calculator.calculate_stats(as_table,
                                                       subprefix_hijack,
                                                       percentage,
                                                       policy)

    @error_catcher()
    def _change_routing_policy(self, percentage, ases, as_table, policy):
        """Changes the routing policy for that percentage of ASes"""

        self.logger.info("About to change the routing policies")
        # Gets the number of ases to change for that percent
        # Could be moved on to the next line but this is cleaner
        number_of_ases_to_change = int(len(ases) * percentage / 100)
        # Gets number of ases to change randomly without duplicates
        ases_to_change = sample(ases, k=number_of_ases_to_change)
        as_table.change_routing_policies(ases_to_change, policy)
        self.logger.debug("Done changing routing policies")

    @error_catcher()
    def _populate_rovpp_mrt_announcements(self, subprefix_hijack):
        """Fill the rovpp mrt announcements table"""

        self.logger.info("Populating rovpp announcements table")
        # I know this is a short function but it's for readability
        with db_connection(ROVPP_MRT_Announcements_Table,
                           self.logger) as mrt_table:
            mrt_table.populate_mrt_announcements(subprefix_hijack)
        self.logger.debug("Done populating rovpp announcements table")
