from unittest.mock import patch

from lib_bgp_data import Simulator
from lib_bgp_data import Relationships_Parser
from lib_bgp_data.utils.database import Database, Generic_Table
from lib_bgp_data.utils import utils
from lib_bgp_data import Non_Default_Policies
from lib_bgp_data.simulations.simulator.data_point_info.test import Test
from lib_bgp_data.simulations.simulator.attacks.attack_classes import Subprefix_Hijack

from datetime import datetime
from lib_bgp_data.simulations.simulator.subtables.subtables_base import Subtables, Subtable
from lib_bgp_data.simulations.simulator.subtables.tables import ASes_Subtable, Subtable_Forwarding_Table
from tqdm import tqdm
from copy import deepcopy
import random
random.seed(0)
percents = [60]

og_test_run = deepcopy(Test.run)
counter = 0


class RemovalASesTable(Generic_Table):
    name = "removal_ases"

    def _create_tables(self):
        sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS {self.name}(
                asn BIGINT
            );"""
        self.execute(sql)
        sql = f"CREATE INDEX IF NOT EXISTS rmas ON {self.name}(asn)"
        self.execute(sql)

def test_run_patch(self, *args, **kwargs):
    """Func to be run once test finishes

    Basically, after the latest round is finished, this runs
    If end condition is reached, do something else
    """

    global counter
    counter += 1
    self.extra_bash_arg_1 = str(counter).zfill(10)

    og_test_run(self, *args, **kwargs)

    sql = """SELECT s1.attacker_asn, s1.victim, s1.trace_hijacked_adopting AS v1_hj, s2.trace_hijacked_adopting AS v2_hj, s1.extra_bash_arg_1 FROM simulation_results s1
            INNER JOIN simulation_results s2
                ON s1.attacker_asn = s2.attacker_asn AND s2.victim = s1.victim
                    AND s1.trace_total_adopting = s2.trace_total_adopting
                    AND s1.trace_total_collateral = s2.trace_total_collateral
            WHERE s1.adopt_pol = 'ROVPP_V1' AND s2.adopt_pol = 'ROVPP_V2'
            ORDER BY s1.extra_bash_arg_1 DESC
          """
    with Database() as db:
        db.execute("CREATE INDEX IF NOT EXISTS simp_index ON sim_test_ases(asn)")
        results = db.execute(sql)
        for result in results:
            # IF v1 has less hijacks than v2
            if result["v1_hj"] < result["v2_hj"]:
                ases_left = set([x["asn"] for x in db.execute("SELECT asn FROM sim_test_ases")])

                dont_delete = set()
                for row in db.execute(f"SELECT peer_as_1 FROM peers WHERE peer_as_2 = {self.attack.attacker} OR peer_as_2 = {self.attack.victim}"):
                    dont_delete.add(row["peer_as_1"])
                for row in db.execute(f"SELECT peer_as_2 FROM peers WHERE peer_as_1 = {self.attack.attacker} OR peer_as_1 = {self.attack.victim}"):
                    dont_delete.add(row["peer_as_2"])
                for row in db.execute(f"SELECT provider_as FROM provider_customers WHERE customer_as = {self.attack.attacker} OR customer_as = {self.attack.victim}"):
                    dont_delete.add(row["provider_as"])
                dont_delete.add(self.attack.attacker)
                dont_delete.add(self.attack.victim)
                ases_left = ases_left.difference(dont_delete)
 
                # Save a reference
                for table_name in ["peers", "provider_customers", "sim_test_ases"]:
                    db.execute(f"DROP TABLE IF EXISTS saved_{table_name}")
                    db.execute(f"CREATE UNLOGGED TABLE saved_{table_name} AS (SELECT * FROM {table_name});")
                    ases_left_saved = deepcopy(ases_left)

                for num_to_remove in [10000, 5000, 2000, 1000, 500, 100, 50, 10, 5, 1]:
                    count_failures = 0
                    while ((count_failures < 20 and num_to_remove >= 5000)
                            or (count_failures < 20 and num_to_remove >= 1000)
                            or (count_failures < 100 and num_to_remove >= 100)
                            or (count_failures < 500 and num_to_remove >= 50)
                            or (count_failures < 1000)):
                        # Not sure if this line will break my fragile script lol
                        # NOTE: THIS LINE MigHt BREAK THINGS????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                        if len(ases_left) < num_to_remove:
                            continue
                        removal_ases = list(random.sample(ases_left, num_to_remove))
                        csv_path = "/tmp/shrinktest.csv"
                        utils.rows_to_db([[x] for x in removal_ases], csv_path, RemovalASesTable)
                        with RemovalASesTable() as db2:
                            print("Removing")
                            db2.execute(f"DELETE FROM peers USING {db2.name} WHERE peer_as_1 = {db2.name}.asn OR peer_as_2 = {db2.name}.asn")
                            print("Removed from peers")
                            db2.execute(f"DELETE FROM provider_customers pc USING {db2.name} r WHERE provider_as = asn OR customer_as = asn")
                            print("Removed from provider customers")
                            db2.execute(f"DELETE FROM sim_test_ases s USING {db2.name} WHERE {db2.name}.asn = s.asn")
                            print("Removal complete")
                        ases_left = list(sorted(set(ases_left).difference(set(removal_ases))))
                        for adopt_pol in [Non_Default_Policies.ROVPP_V1, Non_Default_Policies.ROVPP_V2]:
                            self.adopt_pol = adopt_pol
                            max_count = 10
                            counter += 1
                            self.extra_bash_arg_1 = str(counter).zfill(max_count)
                            og_test_run(self, *args, **kwargs)
                            assert counter < max_count ** 10, "zfill will fail"
                        result = db.execute(sql)[0]
                        print(f"\n\n\n\n\n\n\n\n{len(ases_left_saved)} left\n\n\n\n\n\n\n\n\n")
                        # If alter is successful (v1 still better than v2), save new peers, customer providers, sim test ases, ases left
                        if result["v1_hj"] < result["v2_hj"]:
                            print(f"\n\n\n\n\n\n\n\nSUCCESSFULLY REMOVED {len(removal_ases)}\n\n\n\n\n\n\n\n\n")
                            count_failures = 0
                            for table in ["peers", "provider_customers", "sim_test_ases"]:
                                db.execute(f"DROP TABLE IF EXISTS saved_{table}")
                                db.execute(f"CREATE TABLE saved_{table} AS (SELECT * FROM {table})")
                            ases_left_saved = deepcopy(ases_left)
                        else:
                            count_failures += 1
                            print(f"\n\n\n\n\n\n\n\nFAILED TO REMOVE{len(removal_ases)}\n\n\n\n\n\n\n\n\n")
                            # reset to the old savings
                            for table in ["peers", "provider_customers", "sim_test_ases"]:
                                db.execute(f"DROP TABLE IF EXISTS {table}")
                                db.execute(f"CREATE TABLE {table} AS( SELECT * FROM  saved_{table})")
                            ases_left = deepcopy(ases_left_saved)
                        import sys
                        sys.stdout.flush()
                import sys
                sys.exit()


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

og_redownload = deepcopy(Simulator._redownload_base_data)
def _redownload_base_data_patch(self, *args, **kwargs):
    # forces new install of extrapolator
    print("Later should install exr every time!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    #exr_cls(**self.sim.kwargs).install(force=True)
    Relationships_Parser(**self.kwargs)._run()
    with Database() as db3:
        for sql in ["CREATE INDEX ON peers(peer_as_1)",
                    "CREATE INDEX ON peers(peer_as_2)",
                    "CREATE INDEX ON provider_customers(provider_as)",
                    "CREATE INDEX ON provider_customers(customer_as)"]:
            db3.execute(sql)

with patch.object(Test, "run", test_run_patch):
    with patch.object(Subtables, "get_tables", subtables_get_tables_patch):
        with patch.object(Simulator, "_redownload_base_data", _redownload_base_data_patch):
            Simulator().run(percents=percents,
                            num_trials=20,
                            deterministic=True,
                            attack_types=[Subprefix_Hijack],
                            adopt_policies=[Non_Default_Policies.ROVPP_V1, Non_Default_Policies.ROVPP_V2],
                            redownload_base_data=True)
