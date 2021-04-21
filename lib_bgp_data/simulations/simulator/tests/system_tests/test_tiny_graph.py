#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains system tests for the extrapolator.

For speciifics on each test, see the docstrings under each function.
"""
from datetime import datetime

from unittest.mock import patch
import pytest

from ....enums import Non_Default_Policies, Policies, Data_Plane_Conditions as Conds
from ...attacks.attack_classes import Subprefix_Hijack
from ...attacks.attack import Attack
from ...simulator import Simulator


from .....collectors.relationships.tables import Peers_Table
from .....collectors.relationships.tables import Provider_Customers_Table
from .....collectors.relationships.tables import ASes_Table
from .....collectors.relationships.tables import AS_Connectivity_Table
from .....collectors.as_rank_website.tables import AS_Rank_Table


# Imported for subtables patch
# should go through and delete unnesseccary garbage
from ...simulator import Simulator
from ...subtables.subtables_base import Subtables, Subtable
from ...subtables.tables import ASes_Subtable, Subtable_Forwarding_Table

from .....extrapolator import Simulation_Extrapolator_Wrapper as Sim_Exr
from .....collectors.relationships.tables import Peers_Table, Provider_Customers_Table
from .....utils import utils





__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@pytest.mark.slow
class Test_Tiny_Graph:
    """Tests all example graphs within our paper."""

    def test_tiny_graph(self, max_conn=5, max_lv=2, percents=[1, 15, 30, 50, 80, 99]):
        """Gets the best top 100 AS and goes 1 level out

        max_conn is max number of peers + customers"""

        start = datetime.now()
        sim = Simulator()
        print("MUST REDOWNLOAD EXR HERE")
        sim._redownload_base_data(exr_cls=None)
        with AS_Connectivity_Table() as db:
            ases = [x for x in db.get_all() if x["connectivity"] <= max_conn]
            best_row = max(ases, key=lambda x: x["connectivity"])
            best_as = best_row["asn"]
            print(best_as)
            # Not gonna bother to fix this now since this is temp
            # lol not gonna fix this ever who am I kidding
            sql = """DROP TABLE IF EXISTS links"""
            db.execute(sql)
            sql = """CREATE UNLOGGED TABLE links AS (
                    SELECT peer_as_1 as asn1, peer_as_2 as asn2
                        FROM peers
                    UNION 
                    SELECT provider_as as asn1, customer_as as asn2
                        FROM provider_customers
                    );"""
            db.execute(sql)
            print("created links")
            sql = """DROP TABLE IF EXISTS final_links"""
            db.execute(sql)
            sql = f"""CREATE UNLOGGED TABLE final_links AS (
                    with recursive tr(asn1, asn2, level) as (
                        select links.asn1, links.asn2, 1 as level
                        FROM links
                            WHERE links.asn1 = {best_as} or links.asn2 = {best_as}
                        UNION ALL
                            SELECT links.asn1, links.asn2, tr.level + 1
                                FROM links
                                INNER JOIN tr ON links.asn1 = tr.asn2 OR links.asn2 = tr.asn1
                                    WHERE tr.level < {max_lv})
                        SELECT DISTINCT asn1, asn2 FROM tr
		);"""
            db.execute(sql)
            print("created final links")
            db.execute("ANALYZE")
            print("analyzed")
        # NOTE: this will break if cols are swapped
        with Peers_Table() as db:
            print("deleting from peerS")
            db.execute("DROP TABLE IF EXISTS temp_peers")
            db.execute(f"""ALTER TABLE {db.name} RENAME TO temp_{db.name}""")
            db.execute(f"""CREATE UNLOGGED TABLE {db.name} AS (
                                SELECT peer_as_1, peer_as_2 FROM temp_{db.name} p
                                INNER JOIN final_links f
                                    ON f.asn1 = peer_as_1 AND f.asn2 = peer_as_2);""")
        with Provider_Customers_Table() as db:
            print("deleting from pcs")

            db.execute("DROP TABLE IF EXISTS temp_provider_customers")
            db.execute(f"""ALTER TABLE {db.name} RENAME TO temp_{db.name}""")
            db.execute(f"""CREATE UNLOGGED TABLE {db.name} AS (
                                SELECT provider_as, customer_as FROM temp_{db.name} p
                                INNER JOIN final_links f
                                    ON f.asn1 = provider_as AND f.asn2 = customer_as);""")

            print("creating negative ases") 
            db.execute("""DROP TABLE IF EXISTS negative_ases""")
            db.execute("""CREATE UNLOGGED TABLE negative_ases AS (
                            SELECT asn FROM ases a
                            LEFT JOIN final_links f
                                ON f.asn1 = asn or f.asn2 = asn
                            WHERE f.asn1 IS NULL);""")

        for Tbl in [AS_Rank_Table, ASes_Table, AS_Connectivity_Table]:
            with Tbl() as db:
                print("deleting from tbl")
                db.execute(f"DELETE FROM {db.name} a USING negative_ases n WHERE a.asn = n.asn")





        def subtables_get_tables_patch(subtable_self, *args, **kwargs):
            class Sim_Test_ASes_Table(ASes_Subtable):
                input_name = name = "sim_test_ases"
                columns = ["asn", "as_type", "impliment"]
                def _create_tables(self):
                    sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name} (
                            asn bigint,
                            as_type integer,
                            impliment boolean);
                            """
                    self.cursor.execute(sql)
                def fill_table(self, *args):
                    with ASes_Table() as db:
                        db.execute(f"DROP TABLE IF EXISTS {self.name}")
                        db.execute(f"""CREATE UNLOGGED TABLE {self.name} AS (
                                    SELECT a.asn, {Policies.DEFAULT.value} AS as_type,
                                    FALSE as impliment
                                    FROM {db.name} a);""")

                @property
                def Forwarding_Table(self):
                    return Sim_Test_ASes_Forwarding_Table

            class Sim_Test_ASes_Forwarding_Table(Sim_Test_ASes_Table,
                                                 Subtable_Forwarding_Table):
                name = "sim_test_ases_forwarding"


            subtable_self.tables = [Subtable(Sim_Test_ASes_Table,
                                             percents, #)] #edge_atk, etc_atk, top_atk,
                                             possible_attacker=True)]





        with patch.object(Subtables,
                          "get_tables",
                          subtables_get_tables_patch):
            sim._run(redownload_base_data=False,
                     percents=percents)
