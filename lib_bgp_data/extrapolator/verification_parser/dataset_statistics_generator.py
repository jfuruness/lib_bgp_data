#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class dataset_statistics_generator

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
The purpose of this is to generate input from 3 MRT file sources.
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from copy import deepcopy
import logging
import os
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from shutil import rmtree

from .tables import Monitors_Table, Control_Monitors_Table

from ...collectors import AS_Rank_Website_Parser
from ...collectors.mrt import MRT_Parser, MRT_Metadata_Parser, MRT_Sources
from ...collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table
from ...collectors.relationships.tables import Peers_Table
from ...collectors.relationships.tables import Provider_Customers_Table
from ...utils.base_classes import Parser
from ...utils.database import Database

class Dataset_Statistics_Generator(Parser):
    """This class generates statistics for the dataset

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = ["graph_dir"]

    def __init__(self, *args, **kwargs):
        super(Dataset_Statistics_Generator, self).__init__(*args, **kwargs)
        self.graph_dir = "/tmp/verification_stats_graphs/"
        if os.path.exists(self.graph_dir):
            rmtree(self.graph_dir)
        os.makedirs(self.graph_dir)

    def _run(self):
        for func in [self._get_ripe_route_views_stats,
                     self._get_announcement_stats,
                     self._get_as_rank_stats,
                     self._get_rib_stats,
                     self._get_rib_out_stats,
                     self._get_control_stats,
                     self._get_test_ann_stats,
                     self._get_rel_stats]:
            logging.debug(f"Calling {func}")
            func()
            logging.debug(f"Func {func} complete")

    def _get_ripe_route_views_stats(self):
        """Gets stats on ripe and routeviews

        1. Print time of dataset
        2. Print updates or rip dump
        3. Get collectors for ripe and collectors for routeviews
        4. Get monitors for ripe and monitors for routeviews
        5. Get for each collector, the number of monitors
        """

        pass

    def _get_announcement_stats(self):
        """Gets announcement stats for each monitor

        Plot in decreasing order:
        1. The unique prefix origin pairs for each monitor
        2. The # of ann for each monitor

        side by side in a bar chart
        """

        pass

    def _get_as_rank_stats(self):
        """Gets AS rank stats for each monitor

        Plot in decreasing order the as rank of each monitor
        """

        with Monitors_Table() as db:
            raw_data = list(sorted(db.get_all(), key=lambda x: x["as_rank"]))

        for data_limit in [25, 100, len(raw_data)]:
            data = deepcopy(raw_data)[:data_limit]
            x = np.arange(len(data))
            # Width of the bars
            width = .1 if data_limit > 25 else .2

            fig, ax = plt.subplots()
            rects = ax.bar(x - width / 2, [x["as_rank"] for x in data])

            def autolabel(rects):
                """
                Attach a text label above each bar displaying its height
                """
                for rect in rects:
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                            '%d' % int(height),
                            ha='center', va='bottom', fontsize="10")

            if data_limit <= 25:
                autolabel(rects)

            ax.set_ylabel("AS_Rank")
            ax.set_xlabel("Monitor")
            ax.set_ylim([0, max([x["as_rank"] for x in data]) + 5])
            title = f"Monitor_AS_Rank_stats_{data_limit}_Ases"
            ax.set_title(title.replace("_", " "))

            fig.tight_layout()

            plt.savefig(os.path.join(self.graph_dir, title + ".png"))
            plt.close(fig)


    def _get_rib_stats(self):
        """Get stats for rib in vs rib out

        Plot, in order of extra_ann_multiplier:

        side by side:
        1. Number of prefixes
        2. number of announcements
        3. Number of extra ann multiplier on top

        Plot, in order of duplicates:
        1. Duplicate by prefix
        2. Number of duplicate ann by prefix, origin
        3. Number of duplicate ann by prefix, origin, path
        4. Number of relationships on the top
        """

        pass

    def _get_rib_out_stats(self):
        """Get stats for just rib out

        plot, in order of most prefixes:

        1. total number of prefixes
        2. as rank on top
        """

        pass

    def _get_control_stats(self):
        """Get stats for control monitors

        Plot, in order of po pairs:

        1. total number of prefixes
        2. total number of ann
        3. AS rank
        """

        pass

    def _get_test_ann_stats(self):
        """Get stats for test anns

        print testing metholodogy (intersection of received)

        Plot:

        1. Number of ann omitted
        2. Number of prefixes omitted
        3. Number of ann included
        4. Number of prefixes included
        5. avg # of different path for prefix

        """

        pass

    def _get_rel_stats(self):
        """Get relationship stats

        print relationship date

        plot:
        1. Number of nodes
        2. number of edge ASes
        3. Number of multihomed ASes
        4. Number of transit ases
        5. Number of peer relationship (w/num on top)
        6. Number of provider_customer relationship (w/num on top)
        """


        return
        with Peers_Table() as db:
            logging.debug("Getting number of ases")
            # Number of ASes
            sql = f"""SELECT COUNT(DISTINCT asn) FROM (
                    SELECT peer_as_1 AS asn FROM {Peers_Table.name}
                    UNION ALL
                    SELECT peer_as_2 AS asn FROM {Peers_Table.name}
                    UNION ALL
                    SELECT provider_as AS asn
                        FROM {Provider_Customers_Table.name}
                    UNION ALL
                    SELECT customer_as AS asn
                        FROM {Provider_Customers_Table.name}
                    ) a;"""
            nodes: int = db.get_count(sql)

            logging.debug("Getting number of edges")

            # Number of edges
            # For some reason, forcing the total changes type of join 
            db.execute("ALTER SYSTEM SET enable_nestloop TO 'off';")
            db.execute("SELECT pg_reload_conf();")
            logging.debug("Reloaded db")
            counter = 0
            while "off" not in str(db.execute("SHOW enable_nestloop;")):
                time.sleep(5)
                counter += 1
                assert counter < 10, "Db not reloading properly"
            sql = f"""WITH a AS (
                    SELECT * FROM ( 
                        SELECT asn, COUNT(asn) AS total FROM (
                            SELECT peer_as_1 AS asn FROM {Peers_Table.name}
                            UNION ALL
                            SELECT peer_as_2 AS asn FROM {Peers_Table.name}
                            UNION ALL
                            SELECT customer_as AS asn
                                FROM {Provider_Customers_Table.name}
                            ) a
                        GROUP BY asn) asns
                    LEFT JOIN {Provider_Customers_Table.name} pc
                        ON pc.provider_as = asns.asn
                    WHERE pc.provider_as IS NULL)
                SELECT COUNT(*) FROM a WHERE total = 1;"""
            edges: int = db.get_count(sql)
            logging.debug(edges)

            logging.debug("Getting number of multihomed")
            # Number of multihomed
            sql = f"""WITH totals AS (
                        SELECT customer_as, COUNT(*) AS total FROM (
                            SELECT ogpc.customer_as FROM {Provider_Customers_Table.name} ogpc
                            --for some reason if i do it this way it doesn't use nested left join
                            LEFT JOIN {Provider_Customers_Table.name} pc
                                ON pc.provider_as = ogpc.customer_as
                            WHERE pc.provider_as IS NULL) a
                        GROUP BY customer_as)
                SELECT COUNT(*) FROM totals WHERE total > 1;"""
            multihomed: int = db.get_count(sql)
            logging.debug(multihomed)

            logging.debug("Getting IXPs")
            # Number of IXPs
            sql = f"""WITH totals AS (
                        SELECT peers.asn, COUNT(peers.asn) AS total FROM (
                            SELECT peer_as_1 AS asn FROM {Peers_Table.name}
                            UNION ALL
                            SELECT peer_as_2 AS asn FROM {Peers_Table.name}) peers
                        LEFT JOIN provider_customers pc
                            ON pc.provider_as = peers.asn OR pc.customer_as = peers.asn
                                WHERE pc.provider_as IS NULL
                        GROUP BY peers.asn
                        )
                SELECT COUNT(*) FROM totals WHERE total > 1;"""

            return
            db.execute(f"ANALYZE {Peers_Table.name}")
            db.execute(f"ANALYZE provider_customers")
            #assert False, "Check test.sql change query to be fast"
            ixps: int = db.get_count(sql)
 

            db.execute("ALTER SYSTEM SET enable_nestloop TO 'on';")
            db.execute("SELECT pg_reload_conf();")

            # Simply modify edge sql
            transit: int = nodes - edges - multihomed

            logging.debug("Getting number of peers")
            # Number of peer relationships
            peers: int = db.get_count()
            assert peers > 0, "Peers not populated"

        # Number of provider_customer relationships
        with Provider_Customers_Table() as db:
            logging.debug("Getting number of providers")
            provider_customers: int = db.get_count()
            assert provider_customers > 0, "Provider Customers not populated"

        data_points = {"Total": nodes,
                       "Edge": edges,
                       "Multihomed": multihomed,
                       "Transit": transit,
                       "Peer_Links": peers,
                       "Provider_Customer_Links": provider_customers,
                       "IXPs": ixps}

        logging.debug("Generating graph")
        x = np.arange(len(data_points))
        # Width of the bars
        width = .35

        fig, ax = plt.subplots()
        rects = ax.barh(x - width / 2, list(data_points.values()))

        ax.set_xlabel("ASes")
        ax.set_title("Caida Relationship Statistics")
        ax.set_yticks(x)
        ax.set_xticks(list(range(0, 450001, 150000)))
        ax.set_xlim([0, 450002])
        ax.set_yticklabels(list(data_points.keys()))

        # https://stackoverflow.com/a/30229062
        for i, v in enumerate(list(data_points.values())):
            ax.text(v + 3, i, str(v), fontweight="bold", va="center")
        fig.tight_layout()

        plt.savefig(os.path.join(self.graph_dir, "Relationships_Stats.png"))
        plt.close(fig)
