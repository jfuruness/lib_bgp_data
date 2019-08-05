
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""I am being forced to make all kinds of terrible changes right before the deadline.
this crappy code is not my fault"""


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
from pprint import pprint
from .enums import Policies, Non_BGP_Policies
from .tables import ROVPP_ASes_Table, Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table
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


class ROVPP_Simulator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'percents',
                 'statistics_calculator', 'graph_data']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)
        # Percents from 0, 10, 20 ... 100
        # Later put in the code to run with 0% once for bgp with trials
        # but we already ran this trial so we can take it out for now
        if args.get("percents") is None:
            self.percents = range(5, 31, 5)
        else:
            self.percents = args["percents"]
        args["percents"] = self.percents
        # Define statistics calculator - also where stats are stored
        self.statistics_calculator = ROVPP_Statistics_Calculator(args)
        self.graph_data = Graph_Data(args)

    @error_catcher()
    @utils.run_parser()
    def simulate(self, trials=100, real_data=False):
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
            as_table.fill_table()

            # Gets all ASes within the topology
            ases = {x["asn"]: Policies.BGP.value for x in as_table.get_all()}
            ases_list = list(ases)

            with db_connection(ROVPP_AS_Connectivity_Table,
                               self.logger) as connectivity_table:
                top_100_ases = connectivity_table.get_top_100_ases()
                not_top_100_ases = connectivity_table.get_not_top_100_ases()
                transit_ases, non_transit_ases =\
                    connectivity_table.get_ases_by_transitivity()
                # These are the ases that we choose to change
                list_of_lists_of_ases_to_possibly_impliment = [non_transit_ases]
                # These are the ases that we choose atk and vic from
                bottom_ases = non_transit_ases
                

            # For each percent adoption
            for percent in self.percents:
                # For each trial in that percent
                for i in range(trials):
                    # Note that we do the hijack data here
                    # and security policy implimentation here
                    # Because it should be the same across all policies
                    # for comparison

                    # Gets hijack data
                    subprefix_hijacks = self._get_hijack_data(real_data,
                                                              bottom_ases)

                    # Done here so that the same ases are used between policies
                    ases_to_change = self._get_ases_to_change(
                        percent,
                        list_of_lists_of_ases_to_possibly_impliment,
                        subprefix_hijacks)

                    for policy in Non_BGP_Policies.__members__.values():


                        # Run that specific simulation
                        self._run_simulation(policy.value,
                                             percent,
                                             ases,
                                             ases_to_change,
                                             as_table,
                                             subprefix_hijacks,
                                             i)
        self.graph_data.graph_data(self.statistics_calculator.stats)

########################
### Helper Functions ###
########################

    @error_catcher()
    def _get_relationship_data(self):
        """Gets relationship data, small func ik but makes code cleaner"""

        # Runs relationships parser
        caida_url = "http://data.caida.org/datasets/as-relationships/serial-2/"
        may_data_url = caida_url + "20190501.as-rel2.txt.bz2"
        Relationships_Parser().parse_files(rovpp=True, url=may_data_url)

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
                               self.logger) as fake_data:
                fake_data.populate(ases)
                # Returns all the subprefix hijacks
                return fake_data.execute("SELECT * FROM subprefix_hijack_temp")
            self.logger.debug("Done creating fake data for subprefix hijacks")

    @error_catcher()
    def _run_simulation(self,
                        policy,
                        percentage,
                        ases,
                        ases_to_change,
                        as_table,
                        subprefix_hijacks,
                        trial_num):
        """Runs one single simulation with the extrapolator"""

        self.logger.info("Running policy: {} percent: {} trial: {}".format(
            percentage, policy, trial_num))

        self._change_routing_policy(percentage,
                                    ases,
                                    ases_to_change,
                                    as_table,
                                    policy,
                                    subprefix_hijacks)

        for i, subprefix_hijack in enumerate(subprefix_hijacks):
            self._populate_rovpp_mrt_announcements(subprefix_hijack)
            Extrapolator().run_rovpp(subprefix_hijack["attacker"],
                                     subprefix_hijack["victim"],
                                     subprefix_hijack["more_specific_prefix"])
            self.statistics_calculator.calculate_stats(as_table,
                                                       subprefix_hijack,
                                                       percentage,
                                                       policy)

    @error_catcher()
    def _get_ases_to_change(self,
                            percentage,
                            list_of_lists_of_ases_to_possibly_impliment,
                            subprefix_hijacks):
        ases_to_change = set()
        for ases in list_of_lists_of_ases_to_possibly_impliment:
            # Gets the number of ases to change for that percent
            # Could be moved on to the next line but this is cleaner
            number_of_ases_to_change = int(len(ases) * percentage / 100)
            # Gets number of ases to change randomly without duplicates
            ases_to_change.update(sample(ases, k=number_of_ases_to_change))
            # Makes sure attackers aren't implimenting anything but BGP
            # We can do this because this there are few attacks and lots of asns
            # NOTE: If you ever have a lot of attacks, this will affect results
            for subprefix_hijack in subprefix_hijacks:
                if subprefix_hijack["attacker"] in ases_to_change:
                    ases_to_change.remove(subprefix_hijack["attacker"])
            if int(len(subprefix_hijacks) * 100 / len(ases)) > 1:
                raise Exception("CHANGE THIS CODE YOU IDIOT!!!")

        return ases_to_change


    @error_catcher()
    def _change_routing_policy(self,
                               percentage,
                               ases,
                               ases_to_change,
                               as_table,
                               policy,
                               subprefix_hijacks):
        """Changes the routing policy for that percentage of ASes"""

        self.logger.info("About to change the routing policies")
        # My brain is tired of list comps
        for asn in ases_to_change:
            ases[asn] = policy



        ######################################## TKAE OUT!!!!
#        for asn in ases_to_change:
#            ases[asn] = 'bgp'
        # This is hardcoded bs due to deadline
        hardcoded_bs = [47692,
                        25933,
                        1103,
                        262317,
                        57695,
                        12859,
                        30844,
                        262757,
                        18106,       
                        39122,
                        59605,
                        33891,
                        12389,
                        23106,
                        63927,
                        8492,
                        12552,        
                        31133,
                        264268,
                        8468,
                        42473,
                        36351,
                        30781,
                        34019,
                        28571]
        for asn in hardcoded_bs:
            ases[asn] = 'bgp'

        rows = [[key, value] for key, value in ases.items()]
        # Could we do this in a deep copy dict? Sure but since adoption percentage
        # will probably be low this will prob be faster
        for asn in ases_to_change:
            ases[asn] = Policies.BGP.value
        utils.rows_to_db(self.logger,
                         rows,
                         self.csv_dir + "/ases.csv",
                         ROVPP_ASes_Table)
        #as_table.change_routing_policies(ases_to_change, policy)
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
