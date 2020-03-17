#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Due to lots of last minute decisions in the way we want to run 
our sims, this module has turned into hardcoded crap. Fixing it now."""

from pathos.multiprocessing import ProcessingPool
from multiprocessing import cpu_count
import sys
from math import sqrt
import matplotlib
# https://raspberrypi.stackexchange.com/a/72562
matplotlib.use('Agg')
from matplotlib.transforms import Bbox
from pathos.threading import ThreadPool
import matplotlib.pyplot as plt
from statistics import mean, variance, StatisticsError
from random import sample
from subprocess import check_call
from copy import deepcopy
from pprint import pprint
import json
import os
from tqdm import tqdm
from .enums import Non_BGP_Policies, Policies, Non_BGP_Policies, Hijack_Types, Conditions
from .enums import AS_Types, Control_Plane_Conditions as C_Plane_Conds
from .tables import Subprefix_Hijack_Temp_Table
from .tables import ROVPP_MRT_Announcements_Table, ROVPP_Top_100_ASes_Table
from .tables import ROVPP_Edge_ASes_Table, ROVPP_Etc_ASes_Table, ROVPP_All_Trials_Table
from ..relationships_parser import Relationships_Parser
from ..relationships_parser.tables import AS_Connectivity_Table
from ..bgpstream_website_parser import BGPStream_Website_Parser

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




class ROVPP_Simulator:
    """This class simulates ROVPP.

    In depth explanation at the top of the file
    """


    def __init__(self, section="bgp", args={}):
        """Initializes logger and path variables."""

        # Sets path vars, logger, config, etc
        utils.set_common_init_args(self, args, section, paths=False)
        self.args = args
        # Can't import logging, threadsafe, 20=INFO
        self.args["stream_level"] = self.args.get("stream_level", 20)
        assert False, "In the query below default is bgp. I don't think that's the case any longer. Should be in the files in the relationship_parser/tables.py"
        

#    @utils.run_parser(paths=False)
    def simulate(self,
                 percents=range(5, 31, 5),
                 trials=100,
                 exr_bash=None,
                 exr_test=False,
                 deterministic=False,
                 deterministic_trial=None):
        """Runs ROVPP simulation.

        In depth explanation at top of module.
        """

        # Sets up all trials and percents
        Relationships_Parser(self.args).parse_files(rovpp=True)
        with db_connection(ROVPP_All_Trials_Table, self.logger) as db:
            db.clear_table()

        data_points = [Data_Point(trials, p_i, percent, percents, self.logger)
                       for p_i, percent in enumerate(percents)]

        # NOTE: Make this into a separate function!
        total = 0
        for data_point in data_points:
            for trial in range(data_point.total_trials):
               for test in data_point.get_possible_tests():
                    total += 1
        # Change this later!
        if deterministic and deterministic_trial is not None:
            total = 0
            for data_point in data_points:
               for test in data_point.get_possible_tests():
                    total += 1

        with tqdm(total=total, desc="Running simulator") as pbar:
            for data_point in data_points:
                data_point.get_data(self.args,
                                    pbar,
                                    deterministic,
                                    deterministic_trial,
                                    exr_bash,
                                    exr_test)

        # Close all tables here!!!
        # Graph data here!!!
        # Possibly move back to iterator (below)

    # https://stackoverflow.com/a/1482316
    def powerset_of_policies(self):
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

    def multiprocess_call_to_graphing(self, data_points, hijack_type, pbar, ado_col_list, labelled):
        # This approach takes 4 min 9 seconds if json is loaded with 18 threads
#        try:
            for pol_subset in self.powerset_of_policies():
               # OPEN PROCESS HERE BECAUSE WE CAN HAVE A LOT OPEN DUE TO MOSTLY IO. BUT MUST ALSO WRITE FILES FROM HERE.
               self.gen_ctrl_plane_graphs(data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled)
               self.gen_data_plane_graphs(data_points, hijack_type, pbar, ado_col_list, pol_subset, labelled)
            print(f"{hijack_type}, {ado_col_list}, {labelled} done")
            for fig, path in zip(self.figs, self.fig_paths):
                fig.savefig(path.replace("%", "").replace(" ", "_") + ".png", format="png")
                plt.close(fig)
            print(f"{hijack_type}, {ado_col_list}, {labelled} saved")
            self.figs = []
            self.fig_paths = []
#        except Exception as e:
#            print(f"OOOOOOO {e}")

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
#            X = []
#            Y = []
#            Y_err = []
#            if len(self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["X"]) == 0:
#                for data_point in data_points:
#                    try:
#                        sql = "SELECT " + ", ".join([x + as_type for x in val_strs])
#                        sql += """, trace_total""" + as_type
#                        sql += """ FROM rovpp_all_trials WHERE
#                                   hijack_type = %s AND
#                                   subtable_name = %s AND
#                                   adopt_pol = %s AND
#                                   percent_iter = %s"""
#                        with db_connection(logger=self.logger) as db:
#                            # In the future must not do this in grapher must do this while running
#                            # At 100% adoption attacker is only node left for collateral - not good
#                            query = db.cursor.mogrify(sql, sql_data + [data_point.percent_iter]).decode('UTF-8')
#                            results = db.execute(sql, sql_data + [data_point.percent_iter])
#                            if sql_data[1] == "rovpp_edge_ases" and as_type == "_collateral":
#                                raw = [(sum(x[y + as_type] for y in val_strs) - 1) * 100 / (x["trace_total" + as_type] - 1) for x in results]
#                            else:
#                                raw = [sum(x[y + as_type] for y in val_strs) * 100 / x["trace_total" + as_type] for x in results]    
#                            X.append(data_point.default_percents[data_point.percent_iter])
#                            if data_point.default_percents[data_point.percent_iter] == 0:
#    #                            print("FUCK")
#    #                            print(query)
#                                pass
#                            Y.append(mean(raw))
#                            Y_err.append(1.645 * 2 * sqrt(variance(raw))/sqrt(len(raw)))

#                    except ZeroDivisionError:
#                        continue  # 0 nodes for that
#                    except StatisticsError as e:
#                        self.logger.error(f"Statistics error. {e} Probably need more than one trial for the following query:")
#                        self.logger.error(f"Query: {query}")
#                        self.logger.error(raw)
#                        self.logger.error(results)
#                        sys.exit(1)
#                self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["X"] = X
#                self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["Y"] = Y
#                self.g_dict[h_type][name][pol][plane_type][as_type][str(val_strs)]["YERR"] = Y_err
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


class Data_Point:
    def __init__(self, total_trials, percent_iter, percent,
                 default_percents, logger, _open=True):
        self.total_trials = total_trials
        self.percent_iter = percent_iter
        self.percent = percent
        self.default_percents = default_percents
        self.logger = logger
        self.stats = dict()
        self.tables = Subtables(self.default_percents, self.logger, _open)
        self.logger.debug("Initialized Data Point")

    def get_data(self, exr_args, pbar, seeded, seeded_trial, exr_bash, exr_test):
        self.run_tests(exr_args, pbar, seeded, seeded_trial, exr_bash, exr_test)

    def run_tests(self, exr_args, pbar, seeded, seeded_trial, exr_bash, exr_test):
        for trial in range(self.total_trials):
            if seeded:
                random.seed(trial)
                if seeded_trial and trial != seeded_trial:
                    continue
            for test in self.get_possible_tests(set_up=True, deterministic=seeded):
                test.run(trial, exr_args, pbar, self.percent_iter, exr_bash, exr_test)

    def get_possible_tests(self, set_up=False, deterministic=False):
        for hijack_type in [x.value for x in Hijack_Types.__members__.values()]:
            if set_up:
                hijack = self.set_up_test(hijack_type, deterministic)
            else:
                 hijack = None
            for adopt_pol in [x.value for x in
                              Non_BGP_Policies.__members__.values()]:
                yield Test(self.logger, self.tables, hijack=hijack,
                           hijack_type=hijack_type, adopt_pol=adopt_pol)

    def set_up_test(self, hijack_type, deterministic):
        self.tables = Subtables(self.default_percents, self.logger)
        # sets hijack data
        # Also return hijack variable
        with db_connection(Subprefix_Hijack_Temp_Table, self.logger) as db:
            hijack = db.populate(self.tables.possible_hijacker_ases,
                                 hijack_type)
        self.tables.set_implimentable_ases(self.percent_iter,
                                           hijack.attacker_asn,
                                           deterministic)
        return hijack

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)


class Test:
    def __init__(self, logger, tables, **params):
        self.logger = logger
        self.tables = tables
        self.params = params
        self.hijack = self.params.get("hijack")
        self.hijack_type = self.params.get("hijack_type")
        self.adopt_pol = self.params.get("adopt_pol")
        self.adopt_pol_name = {v.value: k for k, v in
                               Policies.__members__.items()}[self.adopt_pol]
        self.logger.debug("Initialized test")

    def __repr__(self):
        return (self.hijack, self.hijack_type, self.adopt_pol)

    def run(self, trial_num, exr_args, pbar, percent_iter, exr_bash, exr_test):
        # Runs sim, gets data
        pbar.set_description("{}, {}, atk {}, vic {} ".format(
                                    self.hijack_type,
                                    self.adopt_pol_name,
                                    self.hijack.attacker_asn,
                                    self.hijack.victim_asn))
        pbar.refresh()

        self.tables.change_routing_policies(self.adopt_pol)
        # DEBUG = 10, ERROR = 40
        exr_args["stream_level"] = 10 if self.logger.level == 10 else 40
        Extrapolator(exr_args).run_rovpp(self.hijack,
                                         [x.table.name for x in self.tables],
                                         exr_bash,
                                         exr_test,
                                         self.adopt_pol)
        self.tables.store_trial_data(self.hijack,
                                     self.hijack_type,
                                     self.adopt_pol_name,
                                     trial_num,
                                     percent_iter)

        pbar.update(1)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True, indent=4)

class Subtables:
    def __init__(self, default_percents, logger, _open=True):

        self.logger = logger

        # Add docs on how to add a table to these sims
        # Create these tables and then 
        # Create an everything else table
        self.tables = [Subtable(ROVPP_Top_100_ASes_Table,
                                self.logger,
                                default_percents,
                                possible_hijacker=False, _open=_open),
                       Subtable(ROVPP_Edge_ASes_Table,
                                self.logger,
                                default_percents, _open=_open)]
        if _open:
            for sub_table in self.tables:
                sub_table.table.fill_table()

        etc = Subtable(ROVPP_Etc_ASes_Table,
                       self.logger,
                       default_percents,
                       possible_hijacker=False, _open=_open)
        if _open:
            etc.table.fill_table([x.table.name for x in self.tables])
        self.tables.append(etc)
        self.logger.debug("Initialized subtables")

        self._cur_table = -1

    def __len__(self):
        return len(self.tables)

    def __iter__(self):
        return self

    def __next__(self):
        self._cur_table += 1
        try:
            return self.tables[self._cur_table]
        except IndexError:
            self._cur_table = -1
            raise StopIteration

    def close(self):
        # Should really be in the subtable class not here (but for loop should be here)
        for table in self.tables:
            table.close()


    def set_implimentable_ases(self, percent_iteration_num, attacker, deterministic):

        for sub_table in self.tables:
            sub_table.set_implimentable_ases(percent_iteration_num, attacker, deterministic)

    def change_routing_policies(self, policy):
        """Changes the routing policy for that percentage of ASes"""

        # NOTE: maybe make this a new table func with a rename for better speed?
        # TEST IT OUT!!!
        # Also, test index vs no index
        self.logger.debug("About to change the routing policies")
        for sub_table in self.tables:
            sub_table.change_routing_policies(policy)

    @property
    def possible_hijacker_ases(self):
        possible_hijacker_ases = []
        for _table in self.tables:
            if _table.possible_hijacker:
                results = _table.table.get_all()
                for result in results:
                    possible_hijacker_ases.append(result["asn"])
        return possible_hijacker_ases

    def store_trial_data(self, hijack, hijack_type, adopt_pol_name, trial_num, percent_iter):
        # NOTE: Change this later, should be exr_filtered,
        # Or at the very least pass in the args required
        sql = """SELECT asn, received_from_asn, alternate_as FROM
              rovpp_extrapolation_results_filtered;"""
        with db_connection(logger=self.logger) as db:
            ases = {x["asn"]: x for x in db.execute(sql)}
        for table in self.tables:
            table.store_trial_data(ases,
                                   hijack,
                                   hijack_type,
                                   adopt_pol_name,
                                   trial_num,
                                   percent_iter)

class Subtable:
    """Subtable class for ease of use"""

    def __init__(self,
                 table,
                 logger,
                 percents,
                 possible_hijacker=True,
                 policy_to_impliment=None,
                 _open=True):
        self.logger = logger
        if _open is True:
            print("OOO")
        self.table = table(logger, _open=_open)
        self.exr_table_name = "rovpp_exr_{}".format(self.table.name)
        if _open:
            self.count = self.table.get_count()
        self.percents = percents
        self.possible_hijacker = possible_hijacker
        # None for whatever policy is being tested
        self.policy_to_impliment = policy_to_impliment

    def close(self):
        self.table.close()

    def set_implimentable_ases(self, iteration_num, attacker, deterministic):
        self.table.set_implimentable_ases(self.percents[iteration_num],
                                          attacker, deterministic)
    def change_routing_policies(self, policy):
        if self.policy_to_impliment is not None:
            policy = self.policy_to_impliment
        self.table.change_routing_policies(policy)

    def store_trial_data(self, all_ases, hijack, h_type, adopt_pol_name, tnum, percent_iter):
        sql = """SELECT asn, received_from_asn, prefix, origin, alternate_as, impliment FROM {}""".format(self.exr_table_name)
        subtable_ases = {x["asn"]: x for x in self.table.execute(sql)}
        conds = {x.value: {y.value: 0 for y in AS_Types.__members__.values()}
                 for x in Conditions.__members__.values()}
        traceback_data = self._get_traceback_data(deepcopy(conds),
                                                  subtable_ases,
                                                  all_ases,
                                                  hijack,
                                                  h_type,
                                                  adopt_pol_name)
        # Control plane received any kind of prefix that is the same as
        # the attackers, and vice versa
        control_plane_data = {x.value: self._get_control_plane_data(hijack,
                                                                    x.value)
                              for x in AS_Types.__members__.values()}

#        pprint(traceback_data)
#        pprint(control_plane_data)

        with db_connection(ROVPP_All_Trials_Table) as db:
            db.insert(self.table.name,
                      hijack,
                      h_type,
                      adopt_pol_name,
                      tnum,
                      percent_iter,
                      traceback_data,
                      control_plane_data)

    def _get_traceback_data(self, conds, subtable_ases, all_ases, hijack, h_type, adopt_pol_name):
        possible_conditions = set(conds.keys())
        for og_asn, og_as_data in subtable_ases.items():
            # NEEDED FOR EXR DEVS
            looping = True
            asn = og_asn
            as_data = og_as_data
            # Could not use true here but then it becomes very long and ugh
            # SHOULD NEVER BE LONGER THAN 64
            for i in range(64):
                if as_data["received_from_asn"] in possible_conditions:
                    # Preventative announcements
#                    if as_data["alternate_as"] != 0:
#                        if as_data["received_from_asn"] == Conditions.HIJACKED.value:
#                            conds[Conditions.PREVENTATIVEHIJACKED.value][og_as_data["impliment"]] += 1
#                            self.logger.debug("Just hit preventive hijacked in traceback")
#                        else:
#                            conds[Conditions.PREVENTATIVENOTHIJACKED.value][og_as_data["impliment"]] += 1
#                            self.logger.debug("Just hit preventive not hijacked in traceback")
#                    # Non preventative announcements
                            # MUST ADD PREVENTIVE BLACKHOLES - THIS SHOULD JUST TRACE BACK TO ALL CONDITIONS!!!!
#                    else:
                        # TODO: SPELLING WRONG
                     conds[as_data["received_from_asn"]][og_as_data["impliment"]] += 1
                     looping = False
                     break
                else:
                    asn = as_data["received_from_asn"]
                    as_data = all_ases[asn]
            # NEEDED FOR EXR DEVS
            if looping:
                self._print_loop_debug_data(all_ases, og_asn, og_as_data, hijack, h_type, adopt_pol_name)
        ########## ADD STR METHOD TO HIJACK
        return conds

    def _print_loop_debug_data(self, all_ases, og_asn, og_as_data, hijack, h_type, adopt_pol_name):
        class ASN:
            def __init__(self, asn, implimenting):
                self.asn = asn
                self.implimenting = implimenting
            def __repr__(self):
                return f"ASN:{self.asn:<8}: {self.implimenting}"
        debug_loop_list = []
        debug_loop_set = {}
        asn = og_asn
        as_data = og_as_data
        for i in range(64):
            debug_loop_list.append(ASN(asn, as_data["impliment"]))
            asn = as_data["received_from_asn"]
            as_data = all_ases[asn]
            if asn in debug_loop_set:
                loop_strs = ["Loop was found with:",
                             f"Adopt policy: {adopt_pol_name}",
                             f"{hijack}",
                             f"hijack_type: {h_type}",
                             "loop path:",
                             "\t" + "\n\t".join(str(x) for x in debug_loop_list) + "\n"]

                self.logger.error("\n".join(loop_strs))
                sys.exit(1)
            else:
                debug_loop_set.add(asn)

    def _get_control_plane_data(self, hijack, impliment):
        c_plane_data = {}
        sql = "SELECT COUNT(*) FROM " + self.exr_table_name
        sql += " WHERE prefix = %s AND origin = %s AND impliment = " + ("TRUE" if impliment else "FALSE") + ";"
        c_plane_data[C_Plane_Conds.RECEIVED_ATTACKER_PREFIX_ORIGIN.value] =\
            self.table.execute(sql, [hijack.attacker_prefix,
                                     hijack.attacker_asn])[0]["count"]
        c_plane_data[C_Plane_Conds.RECEIVED_ONLY_VICTIM_PREFIX_ORIGIN.value] =\
            self.table.execute(sql, [hijack.victim_prefix,
                                     hijack.victim_asn])[0]["count"]
        c_plane_data[C_Plane_Conds.RECEIVED_BHOLE.value] =\
            self.table.execute(sql, [hijack.attacker_prefix,
                                     Conditions.BHOLED.value])[0]["count"]


        no_rib_sql = """SELECT COUNT(*) FROM {0}
                     LEFT JOIN {1} ON {0}.asn = {1}.asn
                     WHERE {1}.asn IS NULL AND {0}.impliment =
                     """.format(self.table.name, self.exr_table_name)
        c_plane_data[C_Plane_Conds.NO_RIB.value] =\
            self.table.execute(no_rib_sql + ("TRUE" if impliment else "FALSE") + ";")[0]["count"]

        return c_plane_data
