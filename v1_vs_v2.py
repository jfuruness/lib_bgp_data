from unittest.mock import patch

from lib_bgp_data import Simulator
from lib_bgp_data.utils.database import Database
from lib_bgp_data.utils import utils
from lib_bgp_data import Non_Default_Policies
from lib_bgp_data.simulations.simulator.data_point_info.test import Test
from lib_bgp_data.simulations.simulator.attacks.attack_classes import Subprefix_Hijack

from datetime import datetime
from lib_bgp_data.simulations.simulator.subtables.subtables_base import Subtables, Subtable
from lib_bgp_data.simulations.simulator.subtables.tables import ASes_Subtable, Subtable_Forwarding_Table

from copy import deepcopy

percents = [60]

og_test_run = deepcopy(Test.run)

def test_run_patch(self, *args, **kwargs):
    """Func to be run once test finishes

    Basically, after the latest round is finished, this runs
    If end condition is reached, do something else
    """

    og_test_run(self, *args, **kwargs)

    sql = """SELECT s1.attacker_asn, s1.victim, s1.trace_hijacked_adopting AS v1_hj, s2.trace_hijacked_adopting AS v2_hj, s1.extra_bash_arg_1 FROM simulation_results s1
            INNER JOIN simulation_results s2
                ON s1.attacker_asn = s2.attacker_asn AND s2.victim = s1.victim
            WHERE s1.subtable_name = 'edge_ases' AND s2.subtable_name = 'edge_ases' AND s1.adopt_pol = 'ROVPP_V1' AND s2.adopt_pol = 'ROVPP_V2'
            ORDER BY s1.extra_bash_arg_1 DESC
          """
    with Database() as db:
        results = db.execute(sql)
        for result in results:
            # IF v1 has less hijacks than v2
            counter = 0
            if result["v1_hj"] < result["v2_hj"]:
                ases_left = [x["asn"] for x in db.execute("SELECT asn FROM sim_test_ases")]

                # Save a reference
                for table_name in ["peers", "provider_customers", "sim_test_ases"]:
                    db.execute(f"DROP TABLE IF EXISTS saved_{table_name}")
                    db.execute(f"CREATE UNLOGGED TABLE saved_{table_name} AS (SELECT * FROM {table_name});")
                    ases_left_saved = deepcopy(ases_left)

                for num_to_remove in [20000,10000,5000,2500,1000,500,100,50,10,5,1]:
                    for i in range(10):
                        removal_ases = list(random.sample(ases_to_remove, num_to_remove))
                        for asn in removal_ases:
                            db.execute(f"DELETE FROM peers WHERE peer_as_1 = {asn} OR peer_as_2 = {asn}")
                            db.execute(f"DELETE FROM provider_customers WHERE provider_as = {asn} OR customer_as = {asn}")
                            db.execute(f"DELETE FROM sim_test_ases WHERE asn = {asn}")
                        ases_left = list(sorted(set(ases_left).difference(set(ases_to_remove))))
                        for adopt_pol in [Non_Default_Policies.ROVPP_V1, Non_Default_Policies_ROVPP_V2]:
                            max_count = 10 ** 6
                            self.extra_bash_arg_1 = str(counter).zfill(max_count)
                            self.run(*args, **kwargs)
                            counter += 1
                            assert counter < max_count, "zfill will fail"
                        result = db.execute(sql)[0]
                        input("result is highest counter")
                        # If alter is successful (v1 still better than v2), save new peers, customer providers, sim test ases, ases left
                        if result["v1_hj"] < result["v2_hj"]:
                            for table in ["peers", "provider_customers", "sim_test_ases"]:
                                db.execute(f"DROP TABLE IF EXISTS saved_{table}")
                                db.execute(f"CREATE TABLE saved_{table} AS (SELECT * FROM {table})")
                            saved_ases_left = deepcopy(ases_left)
                        else:
                            # reset to the old savings
                            for table in ["peers", "provider_customers", "sim_test_ases"]:
                                db.execute(f"DROP TABLE IF EXISTS {table}")
                                db.execute(f"CREATE TABLE {table} AS( SELECT * FROM  saved_{table})")
                            ases_left = deepcopy(saved_ases_left)
 

                input(f"!\n\n\n\n\n\n\n\n\n\n\n{result}\n\n\n\n\n\n\n!")

############################################################################################
# TODO: patch subtables get_tables
#       should be subtables object with just one table
def subtables_get_tables_patch(subtable_self, percents, *args, **kwargs):
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
            sql = """CREATE UNLOGGED TABLE IF NOT EXISTS sim_test_ases AS (
                    SELECT r.asn, 0 AS as_type, FALSE as impliment FROM ases r);"""
            self.execute(sql)

        @property
        def Forwarding_Table(self):
            return Sim_Test_ASes_Forwarding_Table

    class Sim_Test_ASes_Forwarding_Table(Sim_Test_ASes_Table,
                                         Subtable_Forwarding_Table):
        name = "sim_test_ases_forwarding"


    subtable_self.tables = [Subtable(Sim_Test_ASes_Table,
                                     percents, #)] #edge_atk, etc_atk, top_atk,
                                     possible_attacker=True)]


with patch.object(Test, "run", test_run_patch):
    with patch.object(Subtables, "get_tables", subtables_get_tables_patch):
        Simulator().run(percents=percents,
                        num_trials=20,
                        deterministic=True,
                        attack_types=[Subprefix_Hijack],
                        adopt_policies=[Non_Default_Policies.ROVPP_V1, Non_Default_Policies.ROVPP_V2],
                        redownload_base_data=False)
