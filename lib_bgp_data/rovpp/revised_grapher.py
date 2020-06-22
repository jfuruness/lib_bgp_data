#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Does graphign"""

from .tables import Simulation_Results_Table

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def threadme_bb(data_points, h_type, name, pol_name_dict, pol, as_type, val_strs, X, Y, Y_err, logger, pbar):
    with db_connection(logger=logger) as dbt:
        for data_point in data_points:
            sql_data = [h_type,
            name,
            pol_name_dict[pol]]
            try:
                sql = "SELECT " + ", ".join([x + as_type for x in val_strs])
                sql += """, trace_total""" + as_type
                sql += """ FROM rovpp_all_trials WHERE
                       hijack_type = %s AND
                       subtable_name = %s AND
                       adopt_pol = %s AND
                       percent_iter = %s"""
                # In the future must not do this in grapher must do this while running
                # At 100% adoption attacker is only node left for collateral - not good
                query = dbt.cursor.mogrify(sql, sql_data + [data_point.percent_iter]).decode('UTF-8')
                results = dbt.execute(sql, sql_data + [data_point.percent_iter])
                if sql_data[1] == "rovpp_edge_ases" and as_type == "_collateral":
                    raw = [(sum(x[y + as_type] for y in val_strs) - 1) * 100 / (x["trace_total" + as_type] - 1) for x in results]
                else:
                    raw = [sum(x[y + as_type] for y in val_strs) * 100 / x["trace_total" + as_type] for x in results]
                X.append(data_point.default_percents[data_point.percent_iter])
                if data_point.default_percents[data_point.percent_iter] == 0:
                    pass
                Y.append(mean(raw))
                Y_err.append(1.645 * 2 * sqrt(variance(raw))/sqrt(len(raw)))
            except ZeroDivisionError:
                continue  # 0 nodes for that
            except StatisticsError as e:
                logger.error(f"Statistics error. {e} Probably need more than one trial for the following query:")
                logger.error(f"Query: {query}")
                logger.error(raw)
                logger.error(results)
                sys.exit(1)
            finally:
                pass #pbar.update(1)

    def gen_all_graphs(self, percents_to_graph=None):
        self.generate_agg_tables()
        policy_lines = self.populate_policy_lines()

    def generate_agg_tables(self):
        for Table in [Simulation_Results_Agg_Table,
                      Simulation_Results_Avg_Table]:
            with Table(clear=True) as db:
                db.fill_table()

    def populate_policy_lines(self):
        """Generates all the possible lines on all graphs and fills data"""
        pols, percents, subtables, attacks = self.get_possible_graph_attrs()
        if percents_to_graph is not None:
            percents = [x for x in percents if x in percents_to_graph]
        policy_lines_dict = self.get_policy_lines(pol,
                                                  percents,
                                                  subtables,
                                                  attacks)

        

    def get_possible_graph_attrs(self):
        """Returns all possible graph attributes"""

        with Simulation_Results_Table() as db:
            sql = f"SELECT DISTINCT adopt_pol FROM {db.name}"
            policies = [x["adopt_pol"] for x in db.execute(sql)]
            sql = f"SELECT DISTINCT percent_iter, percent FROM {db.name}"
            percents = [x["percent"] for x in db.execute(sql)]
            err_msg = ("We removed functionality to graph different percents"
                       " at different levels due to the deadline")
            assert len(set(percents)) == len(percents), err_msg
            sql = f"SELECT DISTINCT subtable_name FROM {db.name}"
            subtables = [x["subtable_name"] for x in db.execute(sql)]
            sql = f"SELECT DISTINCT attack_type FROM {db.name}"
            attack_types = [x["attack_type"] for x in db.execute(sql)]

        return policies, percents, subtables, attack_types

    def get_policy_lines(self, policies, percents, subtables, attack_types):
        """Returns every possible policy line class"""

        policy_dict = {}
        for policy in policies:
            for subtable in subtables:
                for attack_type in attack_types:
                    scenario = (policy, subtable, attack_type)
                    for as_type in AS_Types.__members__.values():
                        policy_dict[scenario] = Policy_Line(*scenario,
                                                            as_type.value,
                                                            percents)
        return policy_dict

class Line_Type(Enum):
    DATA_PLANE_HIJACKED = ["trace_hijacked_{}"]
    DATA_PLANE_DISCONNECTED = ["trace_blackholed_{}", "no_rib_{}"]
    DATA_PLANE_SUCCESSFUL_CONNECTION = ["trace_nothijacked_{}"]
    CONTROL_PLANE_HIJACKED = ["c_plane_has_attacker_prefix_origin_{}"]
    CONTROL_PLANE_DISCONNECTED = ["c_plane_has_bhole_{}", "no_rib_{}"]
    CONTROL_PLANE_SUCCESSFUL_CONNECTION =\
        ["c_plane_has_only_victim_prefix_origin_{}"]
    HIDDEN_HIJACK_VISIBLE_HIJACKED = ["visible_hijacks_{}"]
    HIDDEN_HIJACK_HIDDEN_HIJACKED = ["hidden_hijacks_{}"]
    HIDDEN_HIJACK_ALL_HIJACKED = ["trace_hijacked_{}"]

class Graph_Values(Enum):
    X = 0
    Y = 1
    YERR = 2
    STRS = 3

class Policy_Line:
    """This class represents a policy line on a graph"""

    def __init__(self, policy, subtable, attack_type, as_type, percents):
        """Saves class attributes and creates data dict"""

        self.policy = policy
        self.subtable = subtable
        self.attack_type = attack_type
        self.percents = percents
        self.data = {}
        lines_type_enums_strs = [(x, x.value) for x
                                 in Line_Type.__members__.values()]
        for (line_type_enum, line_type_strs) in lines_type_enums_strs:
            for as_type in AS_Types.__members__.values():
                formatted_strs = [x.format(as_type.value) for x in line_type_strs]
                self.data[(line_type_enum,
                           as_type)] = {Graph_Values.X: [],
                                        Graph_Values.Y: [],
                                        Graph_Values.YERR: [],
                                        Graph_Values.STRS: formatted_strs}

    def populate_data(self):
        with Database() as db:
            sql = ""
        for k, data_dict in self.data.items():
            
# This sql will get the aggregate results that we want
sql = """
CREATE UNLOGGED TABLE simulation_results_agg AS (
    SELECT

        attack_type, subtable_name, adopt_pol, percent,

        --adopting traceback
        trace_hijacked_adopting::decimal / trace_total_adopting::decimal AS trace_hijacked_adopting,
        (trace_blackholed_adopting + no_rib_adopting)::decimal / trace_total_adopting::decimal AS trace_disconnected_adopting,
        trace_nothijacked_adopting::decimal / trace_total_adopting::decimal AS trace_connected_adopting,

        --collateral traceback
        trace_hijacked_collateral::decimal / trace_total_collateral::decimal AS trace_hijacked_collateral,
        (trace_blackholed_collateral + no_rib_collateral)::decimal / trace_total_collateral::decimal AS trace_disconnected_collateral,
        trace_nothijacked_collateral::decimal / trace_total_collateral::decimal AS trace_connected_collateral,

        --adopting control plane
        c_plane_has_attacker_prefix_origin_adopting::decimal / trace_total_adopting::decimal AS c_plane_hijacked_adopting,
        (c_plane_has_bhole_adopting + no_rib_adopting)::decimal / trace_total_adopting::decimal AS c_plane_disconnected_adopting,
        c_plane_has_only_victim_prefix_origin_adopting::decimal / trace_total_adopting::decimal AS c_plane_connected_adopting,

        --collateral control plane
        c_plane_has_attacker_prefix_origin_collateral::decimal / trace_total_collateral::decimal AS c_plane_hijacked_collateral,
        (c_plane_has_bhole_collateral + no_rib_collateral)::decimal / trace_total_collateral::decimal AS c_plane_disconnected_collateral,
        c_plane_has_only_victim_prefix_origin_collateral::decimal / trace_total_collateral::decimal AS c_plane_connected_collateral,

        --adopting hidden hijacks
        visible_hijacks_adopting::decimal / trace_total_adopting::decimal AS visible_hijacks_adopting,
        (trace_hijacked_adopting - visible_hijacks_adopting)::decimal / trace_total_adopting::decimal AS hidden_hijacks_adopting,

        --collateral hidden hijacks
        visible_hijacks_collateral::decimal / trace_total_collateral::decimal AS visible_hijacks_collateral,
        (trace_hijacked_collateral - visible_hijacks_collateral)::decimal / trace_total_collateral::decimal AS hidden_hijacks_collateral

    FROM simulation_results
);"""

sql = """
CREATE UNLOGGED TABLE simulation_results_avg AS (
    SELECT
        attack_type, subtable_name, adopt_pol, percent,

        --adopting traceback
        AVG(trace_hijacked_adopting) AS trace_hijacked_adopting,
        (1.645 * 2.0 * STDDEV(trace_hijacked_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_adopting_confidence,
        AVG(trace_disconnected_adopting) AS trace_disconnected_adopting,
        (1.645 * 2.0 * STDDEV(trace_disconnected_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_adopting_confidence,
        AVG(trace_connected_adopting) AS trace_connected_adopting,
        (1.645 * 2.0 * STDDEV(trace_connected_adopting))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_adopting_confidence,
        --collateral traceback
        AVG(trace_hijacked_collateral) AS trace_hijacked_collateral,
        (1.645 * 2.0 * STDDEV(trace_hijacked_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_hijacked_collateral_confidence,
        AVG(trace_disconnected_collateral) AS trace_disconnected_collateral,
        (1.645 * 2.0 * STDDEV(trace_disconnected_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_disconnected_collateral_confidence,
        AVG(trace_connected_collateral) AS trace_connected_collateral,
        (1.645 * 2.0 * STDDEV(trace_connected_collateral))::decimal / SQRT(COUNT(*))::decimal AS trace_connected_collateral_confidence,
        --adopting control plane
        AVG(c_plane_hijacked_adopting) AS c_plane_hijacked_adopting,
        (1.645 * 2.0 * STDDEV(c_plane_hijacked_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_adopting_confidence,
        AVG(c_plane_disconnected_adopting) AS c_plane_disconnected_adopting,
        (1.645 * 2.0 * STDDEV(c_plane_disconnected_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_adopting_confidence,
        AVG(c_plane_connected_adopting) AS c_plane_connected_adopting,
        (1.645 * 2.0 * STDDEV(c_plane_connected_adopting))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_adopting_confidence,
        --collateral control plane
        AVG(c_plane_hijacked_collateral) AS c_plane_hijacked_collateral,
        (1.645 * 2.0 * STDDEV(c_plane_hijacked_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_hijacked_collateral_confidence,
        AVG(c_plane_disconnected_collateral) AS c_plane_disconnected_collateral,
        (1.645 * 2.0 * STDDEV(c_plane_disconnected_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_disconnected_collateral_confidence,
        AVG(c_plane_connected_collateral) AS c_plane_connected_collateral,
        (1.645 * 2.0 * STDDEV(c_plane_connected_collateral))::decimal / SQRT(COUNT(*))::decimal AS c_plane_connected_collateral_confidence,
        --adopting hidden hijacks
        AVG(visible_hijacks_adopting) AS visible_hijacks_adopting,
        (1.645 * 2.0 * STDDEV(visible_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_adopting_confidence,
        AVG(hidden_hijacks_adopting) AS hidden_hijacks_adopting,
        (1.645 * 2.0 * STDDEV(hidden_hijacks_adopting))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_adopting_confidence,
        --collateral hidden hijacks
        AVG(visible_hijacks_collateral) AS visible_hijacks_collateral,
        (1.645 * 2.0 * STDDEV(visible_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS visible_hijacks_collateral_confidence,
        AVG(hidden_hijacks_collateral) AS hidden_hijacks_collateral,
        (1.645 * 2.0 * STDDEV(hidden_hijacks_collateral))::decimal / SQRT(COUNT(*))::decimal AS hidden_hijacks_collateral_confidence
    FROM simulation_results_agg
GROUP BY
    attack_type,
    subtable_name,
    adopt_pol,
    percent
);"""

    # https://stackoverflow.com/a/1482316
    def powerset_of_policies(self, policies=Non_BGP_Policies.__members__.values()):
        from itertools import chain, combinations
        pol_nums = [x.value for x in Non_BGP_Policies.__members__.values()]
        return chain.from_iterable(combinations(pol_nums, r) for r in range(1, len(pol_nums) + 1))

    def multiprocess_call_to_save_fig(self, fig, path, plt):
        fig.savefig(path.replace("%", "").replace(" ", "_") + ".png", format="png")
        plt.close(fig)

    def save_fig(self, fig, path, plt):
        self.graph_pool.amap(self.multiprocess_call_to_save_fig, [fig], [path], [plt])
#        plt.close(fig)

    def gen_all_graphs(self):
        print("Takes ~3.5 hrs to run")
        percents_in_trials = [0,1,2,3,4,5,10,20,30,40,60,80]
        # NOTE save json must be true for all because it only saves X, not what individual points are in it!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#        self.gen_graphs(percents_in_trials, [0,1,2,3,4,5,10], True, "/data/bgp_pics/0_to_10")
#        self.gen_graphs(percents_in_trials, [0,1,2,3,4,5,10, 20, 30], True, "/data/bgp_pics/0_to_30")
        self.gen_graphs(percents_in_trials, [1,10,20,30,40,60,80], False, "/data/bgp_pics/0_to_80")
        print("SET JSON TO TRUE IN LINE ABOVE")
        1/0

#        self.gen_graphs(percents_in_trials, [0,1,2,3,4,5,10,20,30,40,60,80], True, "/data/bgp_pics/0_to_80_all")

    # NOTE: if save_json is false, it will use the OLD JSON FILE!!!!!!
    def gen_graphs(self, percents_in_trials, percents_this_graph, save_json=True, save_dir="/data/bgp_pics"):
        pol_name_dict = {v.value: k for k, v in Non_BGP_Policies.__members__.items()}
        # SHOULD REALLY USE UTILS.POOL!!!
        pool_incrementer = 0
        self.graph_pool = ProcessingPool(18)#cpu_count() * 1.5 + pool_incrementer)
        # NOTE: This is threaded incorrectly - it's the db that should be threaded, but everything is theraded
        self.sql_thread_pool = ThreadPool(nodes=cpu_count() * 1 + pool_incrementer)
        count = 0
        print(utils.now())
        with tqdm(total=12960, desc="Reading in rovpp_all_trials") as pbar:
            utils.clean_paths(self.logger, [save_dir])
            trials = 1
            data_points = [Data_Point(trials, p_i, percent, percents_in_trials, self.logger, _open=False)
                           for p_i, percent in enumerate(percents_in_trials) if percent in percents_this_graph]
#            for data_point in data_points:
#                data_point.tables.close()

            self.pbar = 0
            subtable_names = ["rovpp_top_100_ases", "rovpp_edge_ases", "rovpp_etc_ases"]
            self.g_dict = {x.value: {} for x in Hijack_Types.__members__.values()}
            with tqdm() as pbar2:
                print("Yo if rovpp_all_trials gets too large look out cause you're tryna load the entire thing into mem and multiprocess")
                with db_connection(logger=self.logger) as db:
                    db.cursor.execute("CREATE INDEX IF NOT EXISTS all_trials_index ON rovpp_all_trials(hijack_type, subtable_name, adopt_pol, percent_iter);")
                for h_type in [x.value for x in Hijack_Types.__members__.values()]:
                    self.g_dict[h_type] = {name: {} for name in subtable_names}
                    for name in subtable_names:
                        self.g_dict[h_type][name] = {pol.value: {} for pol in Policies.__members__.values()}
                        for pol in [x.value for x in Non_BGP_Policies.__members__.values()]:
                            self.g_dict[h_type][name][pol] = {"data": {}, "ctrl": {}}
                            for plane_type in ["data", "ctrl"]:
                                for as_type in ["_adopting", "_collateral"]:
                                    self.g_dict[h_type][name][pol][plane_type][as_type] = {}
                                    for val_strs in [["c_plane_has_attacker_prefix_origin"],
                                                     ["c_plane_has_only_victim_prefix_origin"],
                                                     ["c_plane_has_bhole", "no_rib"],
                                                     ["trace_hijacked", "trace_preventivehijacked"],
                                                     ["trace_nothijacked", "trace_preventivenothijacked"],
                                                     ["trace_blackholed", "no_rib"]]:
                                        self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)] = {"X": [], "Y": [], "YERR": []}
                                        X = self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["X"]
                                        Y = self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["Y"]
                                        Y_err = self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["YERR"]
                                        if save_json:
                                            self.sql_thread_pool.amap(threadme_bb, [data_points], [h_type], [name], [pol_name_dict], [pol], [as_type], [val_strs], [X], [Y], [Y_err], [self.logger], [pbar])
                                        continue
                                        1/0 
                                        for data_point in data_points:
                                            sql_data = [h_type,
                                                        name,
                                                        pol_name_dict[pol]]
                                            try:
                                                sql = "SELECT " + ", ".join([x + as_type for x in val_strs])
                                                sql += """, trace_total""" + as_type
                                                sql += """ FROM rovpp_all_trials WHERE
                                                           hijack_type = %s AND
                                                           subtable_name = %s AND
                                                           adopt_pol = %s AND
                                                           percent_iter = %s"""
                                                # In the future must not do this in grapher must do this while running
                                                # At 100% adoption attacker is only node left for collateral - not good
                                                query = db.cursor.mogrify(sql, sql_data + [data_point.percent_iter]).decode('UTF-8')
                                                results = db.execute(sql, sql_data + [data_point.percent_iter])
                                                if sql_data[1] == "rovpp_edge_ases" and as_type == "_collateral":
                                                    raw = [(sum(x[y + as_type] for y in val_strs) - 1) * 100 / (x["trace_total" + as_type] - 1) for x in results]
                                                else:
                                                    raw = [sum(x[y + as_type] for y in val_strs) * 100 / x["trace_total" + as_type] for x in results]
                                                X.append(data_point.default_percents[data_point.percent_iter])
                                                if data_point.default_percents[data_point.percent_iter] == 0:
                        #                            print("FUCK")
                        #                            print(query)
                                                    pass
                                                Y.append(mean(raw))
                                                Y_err.append(1.645 * 2 * sqrt(variance(raw))/sqrt(len(raw)))
                                            except ZeroDivisionError:
                                                continue  # 0 nodes for that
                                            except StatisticsError as e:
                                                self.logger.error(f"Statistics error. {e} Probably need more than one trial for the following query:")
                                                self.logger.error(f"Query: {query}")
                                                self.logger.error(raw)
                                                self.logger.error(results)
                                                sys.exit(1)
                                            finally:
                                                pass#pbar.update(1)
#                                    self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["X"] = X.copy()
#                                    self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["Y"] = Y.copy()
#                                    self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["YERR"] = Y_err.copy()
#                                    pbar.update(1)
    
    

















        print("shoot")
        self.sql_thread_pool.close()
        print("joining")
        self.sql_thread_pool.join()
        self.sql_thread_pool.clear()
        print("To optimize, the above should really be A: Multithreaded or B: output the table into JSON or somsething like that")
        print("Done")
        print(utils.now())
        import json
        if save_json:
            with open('/data/result.json', 'w') as fp:
                json.dump(self.g_dict, fp)

        with open('/data/result.json', 'r') as handle:
            self.g_dict = json.loads(handle.read())

        with tqdm(total=1440 * 9 * 2, desc="Generating subplots") as pbar:



            pol_name_dict = {v.value: k for k, v in Non_BGP_Policies.__members__.items()}

            for labelled in ["labelled", "unlabelled"]:
                for plane_type in ["ctrl", "data", "ctrl_data"]:
                    for ado_col in ["adopting", "collateral", "adopting__collateral"]:
                        for pol_set in self.powerset_of_policies():
                            for htype in [x.value for x in Hijack_Types.__members__.values()]:
                                os.makedirs("{}/{}/{}/{}/{}/{}".format(save_dir, labelled, plane_type, ado_col, "_".join(pol_name_dict[x] for x in pol_set), htype))

            self.figs = []
            self.fig_paths = []

            # SHOULD BE MULTITHREADED!!!
            # OHHHHHHHHH - jk this needs to work differently. The script needs to retain the dict of info to be effective.
            # Get dict of info first, doing only single sets for adopting collateral dataplane hijack type etc. Then gen all graphs. Boom
            # YO - have another thread with tqdm that writes to a progress bar!!!!
            for labelled in ["labelled", "unlabelled"]:
                for ado_col_list in [["_adopting"], ["_collateral"], ["_adopting", "_collateral"]]:
                    print("starting ado col list")
                    for hijack_type in [x.value for x in Hijack_Types.__members__.values()]:
#                        self.multiprocess_call_to_graphing(data_points, hijack_type, pbar, ado_col_list, labelled)
                        
#                        self.graph_pool.amap(self.multiprocess_call_to_graphing, [data_points], [hijack_type], [pbar], [ado_col_list], [labelled])
                        for pol_subset in self.powerset_of_policies():
                            self.graph_pool.amap(self.multiprocess_call_to_graphing2, [data_points], [hijack_type], [pbar], [ado_col_list], [labelled], [pol_subset], [save_dir])
#                            self.multiprocess_call_to_graphing2(data_points, hijack_type, pbar, ado_col_list, labelled, pol_subset)
        print("joining now?")
        self.graph_pool.close()
        print("Just closed")
        self.graph_pool.join()
        self.graph_pool.clear()
        print(utils.now())
        print("It appears that this script leaks like literally 20GB of RAM. Deaadline, but def should be fixed later lmaoooooooooooooooooooo. And they said python couldn't leak memory.")

    def multiprocess_call_to_graphing2(self, data_points, hijack_type, pbar, ado_col_list, labelled, pol_subset, save_dir):

        # Takes ~3 min 39 seconds with 18 threads, same with 24, so I guess lets stick with 18
        # I tried just generating one fig and copying it to multiple processes, but it didn't seem to like that
        # So I removed it
        try:
            # OPEN PROCESS HERE BECAUSE WE CAN HAVE A LOT OPEN DUE TO MOSTLY IO. BUT MUST ALSO WRITE FILES FROM HERE.
            # Potential optimization for the future, make it gen one fig, and pass to each func?
            self.gen_ctrl_plane_graphs(data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled, save_dir)
            self.gen_data_plane_graphs(data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled, save_dir)
            self.gen_ctrl_data_plane_graphs(data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled, save_dir)
#            print(f"{hijack_type}, {ado_col_list}, {labelled} done")
            for fig, path in zip(self.figs, self.fig_paths):
                fig.savefig(path.replace("%", "").replace(" ", "_") + ".png", format="png")
                plt.close(fig)
#            print(f"{hijack_type}, {ado_col_list}, {labelled} saved")
            self.figs = []
            self.fig_paths = []
        except Exception as e:
            print(f"OOOOOOO {e}")


    def gen_ctrl_plane_graphs(self, data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled, save_dir):
        ctrl_val_strs = [["c_plane_has_attacker_prefix_origin"],
                             ["c_plane_has_only_victim_prefix_origin"],
                             ["c_plane_has_bhole", "no_rib"]]
        ctrl_titles = ["Control Plane % Hijacked",
                           "Control Plane % Successful Connection",
                           "Control Plane % Disconnected"]
        self.gen_graph(data_points, ctrl_val_strs, hijack_type, ctrl_titles, "ctrl", pbar, ado_col_list, pol_subset, labelled, save_dir)

    def gen_data_plane_graphs(self, data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled, save_dir):
        data_val_strs = [["trace_hijacked", "trace_preventivehijacked"],
                             ["trace_nothijacked", "trace_preventivenothijacked"],
                             ["trace_blackholed", "no_rib"]]
        data_titles = ["Data Plane % Hijacked",
                           "Data Plane % Successful Connection",
                           "Data Plane % Disconnected"]
        self.gen_graph(data_points, data_val_strs, hijack_type, data_titles, "data", pbar, ado_col_list, pol_subset, labelled, save_dir)

    def gen_ctrl_data_plane_graphs(self, data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled, save_dir):

        data_val_strs = [["trace_hijacked", "trace_preventivehijacked"],
                             ["trace_nothijacked", "trace_preventivenothijacked"],
                             ["trace_blackholed", "no_rib"]]
        data_titles = ["% Hijacked",
                       "% Successful Connection",
                       "% Disconnected"]
        ctrl_val_strs = [["c_plane_has_attacker_prefix_origin"],
                             ["c_plane_has_only_victim_prefix_origin"],
                             ["c_plane_has_bhole", "no_rib"]]
        ctrl_titles = ["% Hijacked",
                           "% Successful Connection",
                           "% Disconnected"]



        fig, axs = plt.subplots(len(ctrl_val_strs), len(data_points[0].tables))
        fig.set_size_inches(18.5, 10.5)
        fig.tight_layout()
        pol_name_dict = {v.value: k for k, v in Non_BGP_Policies.__members__.items()}
        val_strs_list = ctrl_val_strs
        titles = ctrl_titles
        g_title="ctrl"        
        for i, table in enumerate(data_points[0].tables):
            for j, vals in enumerate(zip(val_strs_list, titles)):
                # Graphing Hijacked
                ax = axs[i,j]
                ax.set_ylim(0, 100)
                # Needed due to annoying error https://stackoverflow.com/a/19640319
                ax.set_rasterized(True)
                legend_vals = []
                for pol in pol_subset:#[x.value for x in Non_BGP_Policies.__members__.values()]:
                    sql_data = [hijack_type,
                                table.table.name,
                                pol_name_dict[pol]]
                    self._gen_subplot(data_points, vals[0], sql_data, ax, hijack_type, vals[1], pol_name_dict[pol], pbar, pol, ado_col_list, g_title, table.table.name, hijack_type, labelled, plane_legend="ctrl")



        val_strs_list = data_val_strs
        titles = data_titles
        g_title="data"
        save_path = "{}/{}/{}/{}/{}/{}".format(save_dir, labelled, "ctrl_data", "_".join(ado_col_list)[1:], "_".join(pol_name_dict[x] for x in pol_subset), hijack_type).replace("%", "").replace(" ", "_")
        for i, table in enumerate(data_points[0].tables):
            for j, vals in enumerate(zip(val_strs_list, titles)):
                # Graphing Hijacked
                ax = axs[i,j]
                # Needed due to annoying error https://stackoverflow.com/a/19640319
                ax.set_rasterized(True)
                ax.set_ylim(0, 100)
                legend_vals = []
                for pol in pol_subset:#[x.value for x in Non_BGP_Policies.__members__.values()]:
                    sql_data = [hijack_type,
                                table.table.name,
                                pol_name_dict[pol]]
                    self._gen_subplot(data_points, vals[0], sql_data, ax, hijack_type, vals[1], pol_name_dict[pol], pbar, pol, ado_col_list, g_title, table.table.name, hijack_type, labelled, plane_legend="data")




                # Must be done here so as not to be set twice
                ax.set(xlabel="% adoption", ylabel=vals[1])
                if labelled == "labelled":
#                    ax.title.set_text("{} for {}".format(table.table.name, hijack_type))
                    if "hijacked" in vals[1].lower():
                        loc="lower left"
                    else:
                        loc = "upper left"

                    ax.legend(loc=loc)
                # Needed so that subplots don't overlap, takes time tho fix later
                fig.tight_layout()
                # https://stackoverflow.com/a/26432947
                extent = self.full_extent(ax).transformed(fig.dpi_scale_trans.inverted())
                fig.savefig(os.path.join(save_path, vals[1] + "_" + table.table.name).replace("%", "").replace(" ", "_") + ".png", bbox_inches=extent, format="png")

#                ax.title.set_text(table.table.name)
#                plt.ylabel("{} for {}".format(g_title, hijack_type), axes=ax)
#                plt.xlabel("% adoption", axes=ax)
        fig.tight_layout()
#        plt.shoiw()
        plane_type = "ctrl_data"
        g_title="ctrl_data"
        # /data/bgp_pics/plane_type/ado_col/policies/graph_title
        save_path = "{}/{}/{}/{}/{}".format(save_dir, labelled, g_title, "_".join(ado_col_list)[1:], "_".join(pol_name_dict[x] for x in pol_subset)).replace("%", "").replace(" ", "_")
        self.figs.append(fig)
        self.fig_paths.append(os.path.join(save_path, "{}_{}".format(g_title, hijack_type)))

    # https://stackoverflow.com/a/26432947
    def full_extent(self, ax, pad=0.0):
        """Get the full extent of an axes, including axes labels, tick labels, and
        titles."""
        # For text objects, we need to draw the figure first, otherwise the extents
        # are undefined.
        ax.figure.canvas.draw()
        items = ax.get_xticklabels() + ax.get_yticklabels() 
    #    items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
        # NEED TO CHANGE CROPPING BY TYPE OF GRAPH
        items += [ax, ax.title]
        items += [ax.get_xaxis().get_label(), ax.get_yaxis().get_label()]
        bbox = Bbox.union([item.get_window_extent() for item in items])
        extent = bbox.expanded(1.0 + pad, 1.0 + pad)
        extent.x0 -= 5
        extent.x1 -= 25
        return extent 


    def gen_graph(self, data_points, val_strs_list, hijack_type, titles, g_title, pbar, ado_col_list, pol_subset, labelled, save_dir):
        fig, axs = plt.subplots(len(val_strs_list), len(data_points[0].tables))
        fig.set_size_inches(18.5, 10.5)
        fig.tight_layout()
        pol_name_dict = {v.value: k for k, v in Non_BGP_Policies.__members__.items()}
        # /data/bgp_pics/plane_type/ado_col/policies/overall_graph_title/graph_titles
        save_path = "{}/{}/{}/{}/{}/{}".format(save_dir, labelled, g_title, "_".join(ado_col_list)[1:], "_".join(pol_name_dict[x] for x in pol_subset), hijack_type).replace("%", "").replace(" ", "_")
        for i, table in enumerate(data_points[0].tables):
            for j, vals in enumerate(zip(val_strs_list, titles)):
                # Graphing Hijacked
                ax = axs[i,j]
                # Needed due to annoying error https://stackoverflow.com/a/19640319
                ax.set_rasterized(True)
                ax.set_ylim(0, 100)
                legend_vals = []
                for pol in pol_subset:#[x.value for x in Non_BGP_Policies.__members__.values()]:
                    sql_data = [hijack_type,
                                table.table.name,
                                pol_name_dict[pol]]
                    self._gen_subplot(data_points, vals[0], sql_data, ax, hijack_type, vals[1], pol_name_dict[pol], pbar, pol, ado_col_list, g_title, table.table.name, hijack_type, labelled)
                # Must be done here so as not to be set twice
                ax.set(xlabel="% adoption", ylabel=vals[1])
                if labelled == "labelled":
#                    ax.title.set_text("{} for {}".format(table.table.name, hijack_type))
                    if "hijacked" in vals[1].lower():
                        loc="lower left"
                    else:
                        loc = "upper left"

                    ax.legend(loc=loc)
                # Needed so that subplots don't overlap, takes time though fix later
                fig.tight_layout()
                # https://stackoverflow.com/a/26432947
                extent = self.full_extent(ax).transformed(fig.dpi_scale_trans.inverted())
                fig.savefig(os.path.join(save_path, vals[1] + "_" + table.table.name).replace("%", "").replace(" ", "_") + ".png", bbox_inches=extent, format="png")
                # Force Y to go between 0 and 100
#                ax.set_ylim(0, 100)
#                ax.title.set_text(table.table.name)
#                plt.ylabel("{} for {}".format(g_title, hijack_type), axes=ax)
#                plt.xlabel("% adoption", axes=ax)
        fig.tight_layout()
#        plt.shoiw()
        plane_type = g_title
        self.figs.append(fig)
        save_path = "{}/{}/{}/{}/{}".format(save_dir, labelled, g_title, "_".join(ado_col_list)[1:], "_".join(pol_name_dict[x] for x in pol_subset)).replace("%", "").replace(" ", "_")
        self.fig_paths.append(os.path.join(save_path, "{}_{}".format(g_title, hijack_type)))
#        fig.savefig(os.path.join(save_path, "{}_{}".format(g_title, hijack_type)))
#        self.save_fig(fig, save_path, plt)

    def _gen_subplot(self, data_points, val_strs, sql_data, ax, hijack_type, title, adopt_pol, pbar, pol, ado_col_list, plane_type, name, h_type, labelled, plane_legend=""):
        for as_type in ado_col_list:
            styles = ["-", "--", "-.", ":", "solid", "dotted", "dashdot", "dashed"]
            markers = [".", "1", "*", "x", "d", "2", "3", "4"]
            assert pol < len(styles), "Must add more styles, sorry no time deadline"
            labels_dict = {"ROV": "ROV",
                           "ROVPP": "ROV++v1",
                           "ROVPPB": "ROV++v2a",
                           "ROVPPBP": "ROV++v3",
                           "ROVPPBIS": "ROV++v2"}
#            print(self.g_dict[h_type][name])
            # JSON messed up converts to str which is why this is all messed up with casts
            line = ax.errorbar(self.g_dict[h_type][name][str(pol)][plane_type][as_type][str(val_strs)]["X"],
                               self.g_dict[h_type][name][str(pol)][plane_type][as_type][str(val_strs)]["Y"],
                               yerr=self.g_dict[h_type][name][str(pol)][plane_type][as_type][str(val_strs)]["YERR"], label=labels_dict[adopt_pol] + as_type + " " + plane_legend, ls=styles[int(pol)], marker=markers[int(pol)])
#        pbar.update(1)
        self.pbar += 1

