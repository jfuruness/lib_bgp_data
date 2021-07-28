#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Extrapolator_Analyzer

The purpose of this class is to run the extrapolator verification.
For more info see: https://github.com/c-morris/BGPExtrapolator
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness", "James Breslin"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"



from .tables import Monitors_Table, Control_Monitors_Table

from ..wrappers import Extrapolator_Wrapper

from ...collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table
from ...collectors.relationships.tables import Peers_Table
from ...collectors.relationships.tables import Provider_Customers_Table
from ...utils.base_classes import Parser
from ...utils.database import Database


class Extrapolator_Analyzer(Parser):
    """This class generates input to the extrapolator verification

    In depth explanation at the top of module. Jk needs docs
    """

    __slots__ = []

    def _run(self, test):
        with Control_Monitors_Table() as db:
            table = "mrt_w_metadata"
            if test:
                db.execute("DROP TABLE IF EXISTS mrt_verif_test")
                db.execute(f"""CREATE TABLE mrt_verif_test AS (
                            SELECT * FROM mrt_w_metadata WHERE block_id <= 100);""")
                table = "mrt_verif_test"
            rows = db.get_all()
            final_results = {}
            for row in rows:
                final_results[row['asn']] = {}
                exr_rows = []
                output_tables = []
                for origin_only_mode, mh_prop in [[0, 0],
                                                  [1, 0],
                                                  [0, 1]]:
                    output_table = f"verification_origin_only{origin_only_mode}_mh_{mh_prop}"
                    output_tables.append(output_table)
                    cmd = (f"time /usr/bin/master_extrapolator ")
                    cmd += f"-a {table} --store-results=0 "
                    cmd += (f"--full-path-asns {row['asn']} "
                            f"--exclude-monitor={row['asn']} "
                            f"--mh-propagation-mode={mh_prop} "
                            f"--origin-only={origin_only_mode} "
                            f"--log-folder=/tmp/exr-log --log-std-out=1 "
                            f"--select-block-id=1 "
                            f"--full-path-results-table {output_table}")
                    Extrapolator_Wrapper(**self.kwargs)._run(bash_args=cmd)
                with Database() as db:
                    db.execute("DROP TABLE IF EXISTS control_data")
                    sql = f"""CREATE UNLOGGED TABLE control_data AS (
                            SELECT * FROM {table}
                                WHERE monitor_asn = %s);"""
                    db.execute(sql, [row['asn']])
                    
                    print("Created control tbl")
                    for output_table in output_tables:
                        # I know this isn't the fastest way, but whatevs
                        # It's fast enough compared to the runtime of the exr
                        sql = f"""SELECT ctrl.as_path AS ground_truth,
                                        out.as_path AS estimate
                                    FROM control_data ctrl
                                LEFT JOIN {output_table} out
                                    ON out.prefix_id = ctrl.prefix_id"""
                        results = (db.execute(sql))
                        distances = []
                        from tqdm import tqdm
                        # NOTE: if this is too slow, use the python-levenshtein for a c version
                        # And just convert ints to strs
                        for result in tqdm(results, total=len(results), desc="calculating levenshtein"):
                            if result["estimate"] is None:
                                distances.append(len(result["ground_truth"]))
                            else:
                                distances.append(self.levenshtein(result["ground_truth"], result["estimate"]))

                        from statistics import mean
                        final_results[row['asn']][output_table] = mean(distances)
                        from pprint import pprint
                        pprint(final_results)
                    agg_dict = {}
                    for _, outcomes in final_results.items():
                        for outcome_table, distance in outcomes.items():
                            agg_dict[outcome_table] = agg_dict.get(outcome_table, []) + [distance]
                    for outcome_table, outcome_list in agg_dict.items():
                        agg_dict[outcome_table] = mean(outcome_list)
                    pprint(agg_dict)
                        

    # https://stackoverflow.com/a/6709779/8903959
    def levenshtein(self, a,b):
        "Calculates the Levenshtein distance between a and b."
        n, m = len(a), len(b)
        if n > m:
            # Make sure n <= m, to use O(min(n,m)) space
            a,b = b,a
            n,m = m,n
            
        current = range(n+1)
        for i in range(1,m+1):
            previous, current = current, [i]+[0]*n
            for j in range(1,n+1):
                add, delete = previous[j]+1, current[j-1]+1
                change = previous[j-1]
                if a[j-1] != b[i-1]:
                    change = change + 1
                current[j] = min(add, delete, change)
                
        return current[n]
