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
2. The bgpstream_website_parser is run

    -Handled in _multiprocess_download function
    -This instantiates the mrt_file class with each url
        -utils.download_file handles downloading each particular file
    -Four times the CPUs is used for thread count since it is I/O bound
        -Mutlithreading with GIL lock is better than multiprocessing
         since this is just intesive I/O in this case
    -Downloaded first so that we parse the largest files first
    -In this way, more files are parsed in parallel (since the largest
     files are not left until the end)
3. Then all mrt_files are parsed in parallel
    -Handled in _multiprocess_parse_dls function
    -The mrt_files class handles the actual parsing of the files
    -CPUs - 1 is used for thread count since this is a CPU bound process
    -Largest files are parsed first for faster overall parsing
    -Parsing with bgpscanner is faster, but ignores malformed
     announcements. Use this for testing, and bgpdump is used for full
     runs
4. Parsed information is stored in csv files, and old files are deleted
    -This is handled by the mrt_file class
    -This is done because there is thirty to one hundred gigabytes
        -Fast insertion is needed, and bulk insertion is the fastest
    -CSVs are chosen over binaries even though they are slightly slower
        -CSVs are more portable and don't rely on postgres versions
        -Binary file insertion relies on specific postgres instance
    -Old files are deleted to free up space
5. CSV files are inserted into postgres using COPY, and then deleted
    -This is handled by mrt_file class
    -COPY is used for speedy bulk insertions
    -Files are deleted to save space
    -Duplicates are not deleted because this is an intensive process
        -There are not a lot of duplicates, so it's not worth the time
        -The overall project takes longer if duplicates are deleted
        -A duplicate has the same AS path and prefix
6. VACUUM ANALYZE is then called to analyze the table for statistics
    -An index is never created on the mrt announcements because when
     the announcements table is intersected with roas table, only a
     parallel sequential scan is used

Design choices (summarizing from above):
    -We only want the first BGP dump
        -Multiple dumps have conflicting announcements
        -Instead, for longer intervals use one BGP dump and updates
    -Due to I/O bound downloading:
        -Multithreading is used over multiprocessing for less memory
        -Four times CPUs is used for thread count
    -I have a misquito bite that is quite large.
    -Downloading is done and completed before parsing
        -This is done to ensure largest files get parsed first
        -Results in fastest time
    -Downloading completes 100% before parsing because synchronization
     primitives make the program slower if downloading is done until
     threads are available for parsing
    -Largest files are parsed first because due to the difference in
     in file size there is more parallelization achieved when parsing
     largest files first resulting in a faster overall time
    -CPUs - 1 is used for thread count since the process is CPU bound
        -For our machine this is the fastest, feel free to experiment
    -Parsing with bgpscanner is faster, but ignores malformed
     announcements. Use this for testing, and bgpdump is used for full
     runs
    -Data is bulk inserted into postgres
        -Bulk insertion using COPY is the fastest way to insert data
         into postgres and is neccessary due to massive data size
    -Parsed information is stored in CSV files
        -Binary files require changes based on each postgres version
        -Not as compatable as CSV files
    -Duplicates are not deleted to save time, since there are very few
        -A duplicate has the same AS path and prefix
    -Announcements with malformed attributes are disregarded thanks to
     bgpscanner

Possible Future Extensions:
    -Add functionality to download and parse updates?
        -This would allow for a longer time interval
        -After the first dump it is assumed this would be faster?
        -Would need to make sure that all updates are gathered, not
         just the first in the time interval to the api, as is the norm
    -Test again for different thread numbers now that bgpscanner is used
    -Add test cases
"""

from random import randint
from subprocess import call
from ..relationships_parser import Relationships_Parser
from ..bgpstream_website_parser import BGPStream_Website_Parser
from ..utils import Database, Config, error_catcher

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "Reynaldo"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# enum because strings shouldn't just be being passed around
class Routing_Policies(Enum):
    """The three types of routing policies"""

    BGP = "bgp"
    ROV = "rov"
    ROVPP = "rovpp"


class ROVPP_Simulator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """

    __slots__ = ['path', 'csv_dir', 'logger', 'start_time', 'success_rates']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args)

    @error_catcher()
    @utils.run_parser()
    def simulate(self)
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Runs relationships_parser
        self._get_relationship_data()
        # Runs bgpstream_website_parser
        self._get_hijack_data()
                
        # Populates table
        with db_connection(ROVPP_ASes_Table, self.logger) as as_table:
            # Gets all ASes within the topology
            ases = [x["asn"] for x in 
                    as_table.execute("SELECT * FROM rovpp_ases")]
            # Gets the routing policies to try
            # Because 100%bgp is the default
            non_bgp_policies = [x for x in Policies.__members__.values()
                                if x != Policies.BGP]
            # Defines the success rates.
            # Could be done in list comp but this is more readable
            self.success_rates = dict()
            percentages = range(101)
            for policy in non_bgp_policies:
                for percent in percentages:
                    self.success_rates[policy] = dict()
                    self.success_rates[policy][percent] = []
                    self._run_simulation(policy, percentage, ases, as_table)

########################
### Helper Functions ###
########################

    @error_catcher()
    def _run_simulation(self, policy, percentage, ases, as_table):
        """Runs one single simulation with the extrapolator"""

        self._change_routing_policy(percentage, ases, as_table, policy)
        subprefix_hijacks = as_table.execute("SELECT * FROM subprefix_hijacks")
        for subprefix_hijack in subprefix_hijacks:
            self._populate_rovpp_mrt_announcements(as_table, subprefix_hijack)
            self._run_extrapolator(subprefix_hijack)
            success_rate = self._calculate_success(subprefix_hijack)
            success_rates[policy][percentage].append(success_rate)

    @error_catcher()
    def _run_extrapolator(self, hijack):
        """Runs extrapolator with a subprefix hijack"""

        # Run the extrapolator
        bash_args = ".{} ".format(Config(self.logger).rovpp_extrapolator_path)
        # Don't invert the results so that we have the last hop
        bash_args += "--invert-results=0 "
        # Gives the attacker asn
        bash_args += "--attacker_asn={} ".format(hijack["attacker"])
        # Gives the victim asn
        bash_args += "--victim-asn={} ".format(hijack["victim"])
        # Gives the more specific prefix that the attacker sent out
        bash_args += "--victim_prefix={}".format(hijack["expected_prefix"])

        call(bash_args, shell=True)

    @error_catcher()
    def _populate_rovpp_mrt_announcements(self, subprefix_hijack):
        """Fill the rovpp mrt announcements table"""

        # I know this is a short function but it's for readability
        with db_connection(ROVPP_MRT_Announcements_Table) as mrt_table:
            mrt_table.populate_mrt_announcements(subprefix_hijack) 

    @error_catcher()
    def _calc_success_rate(self, as_table, subprefix_hijack):
        """Calculates success rates"""

        # Returns a dictionary of ases by policy in the enum
        # Filters out the attacker and the victim from the results 
        ases_dict = self._get_ases(subprefix_hijack)
        for policy, policy_ases in ases_dict.items():
            # Calc for all three then general case
            # if someone has the hijack they lose
            # else, go back from last hop, when reach attacker or victim quit
            # attacker = success, victim = fail
            #####################################################LEFT TO DO:
            # do the notes above
            # aferage out the success rates
            # print the success rates
            # put the success rates into some kind of a plot
        

    @error_catcher()
    def _get_ases(self, as_table, subprefix_hijack):
        """EXCLUDES ATTACKER AND VICTIM ASES"""

        ases = {policy: [] for policy in Policies.__members__.values()}
        for policy in Policies.__members__.values(): 
            sql = """SELECT * FROM rovpp_extrapolator_results exr
                     LEFT JOIN SELECT * FROM rovpp_ases ases
                     ON ases.origin = exr.origin
                     WHERE as_type = %s"""
            for _as in as_table.execute(sql, [policy]):
                # Makes sure that the attacker and victim are not included
                for i in ["victim", "attacker"]:
                    if _as = subprefix_hijack[i]:
                        continue
                ases[policy].append(_as)
        return ases

    @error_catcher()
    def _get_relationship_data(self):
        """Gets relationship data, small func ik but makes code cleaner"""

        # Runs relationships parser
        caida_url = "http://data.caida.org/datasets/as-relationships/serial-2/"
        may_data_url = caida_url + "20190501.as-rel2.txt.bz2"
        Relationships_Parser.parse_files(self, rovpp=True, url=may_data_url)

    @error_catcher()
    def _get_hijack_data(self):
        """Gets bgpstream data, small fun ik but makes code cleaner"""

        # Runs the bgpstream_website parser        
        BGPStream_Website_Parser().parse(start='2019-05-07 00:00:00',
                                         end='2019-05-07 00:00:00')


    @error_catcher()
    def _change_routing_policy(self, percentage, ases, as_table, policy):
        """Changes the routing policy for that percentage of ASes"""

        # ases to change for this run
        ases_to_change = set()
        # Gets the number of ases to change for that percent
        # Could be moved on to the next line but this is cleaner
        number_of_ases_to_change = int(len(ases) * percentage / 100)
        for r in range(number_of_ases_to_change):
            # Prevents duplicates
            set_len = len(ases_to_change)
            # To prevent duplicates from being added
            while(len(ases_to_change) == set_len):
                ases_to_change.add(ases[randint(0, r)]["asn"])
        as_table.change_routing_policies(ases_to_change, policy) 
