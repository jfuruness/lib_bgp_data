#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains What_if_analsyis to run policies on mrt_announcements"""

import http.server
import socketserver
from multiprocess import Process
import functools
from contextlib import contextmanager
import os
from subprocess import Popen
import time
import urllib
from ..logger import Logger, error_catcher
from .. import utils
from .tables import Unique_Prefix_Origins_Table, Validity_Table
from ..database import Database

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Justin Furuness", "Cameron Morris"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

# This decorator wraps any run policy function to write to a csv and db insert
# This starts the run policy, cleans all paths, ends the parser, and records time
# The point of this decorator is to make sure the policy runs smoothly
def run_policy():
    def my_decorator(run_policy_func):
        @functools.wraps(run_policy_func)
        def function_that_runs_func(self, *args, **kwargs):
            # Inside the decorator

            # Gets the start time
            start_time = utils.now()
            # Deletes everything from and creates paths
            utils.clean_paths(self.logger, self.all_files)
            try:
                # Runs the parser
                rows, csv_path, table = run_policy_func(self, *args, **kwargs)
                utils.write_csv(self.logger, rows, csv_path)
                utils.csv_to_db(self.logger, table, csv_path)

            # Upon error, log the exception
            except Exception as e:
                self.logger.error(e)
                raise e
            # End the parser to delete all files and directories always
            finally:
                # Clean up don't be messy yo
                utils.end_parser(self.logger, self.all_files, start_time)
        return function_that_runs_func
    return my_decorator

@contextmanager
def _serve_file(self, path):
    p = Process(target=self._serve_file, args=(path, ))
    p.start()
    yield 
    p.terminate()
    p.join()

@contextmanager
def _run_rpki_validator(self, file_path, rpki_path):
    with _serve_file(self, file_path):
        process = Popen([rpki_path])
        yield 
        process.terminate()

#TODO Add to docs valid=1, unknown=0, invalid=-1


class What_if_Analysis:
    """This class runs all the policies on the mrt_announcements table""" 

    __slots__ = ['path', 'csv_dir', 'args', 'logger', 'csv_path', 'all_files']

    @error_catcher()
    def __init__(self, args={}):
        """Initializes urls, regexes, and path variables"""

        # Sets common file paths and logger
        utils.set_common_init_args(self, args, "What If Analysis")
        

    @error_catcher()
    @utils.run_parser()
    def run_policies(self, db=True):
        """Downloads and stores roas from a json"""

        unique_p_o = Unique_Prefix_Origins_Table(self.logger)
#        unique_p_o.fill_table()
        rpki_path = "/justins_validator/dev/rpki-validator-3.0-DEV20180902182639/rpki-validator-3.sh"
#        new_path, total_rows = unique_p_o.write_validator_file(
#                                    path="/tmp/validator.csv")#.format(self.path))
        new_path = "/tmp/validator.csv.gz"
        total_rows = 900000
        headers = {"Connection": "keep-alive","Cache-Control": "max-age=0", "Upgrade-Insecure-Requests": 1,"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9"}
        with _run_rpki_validator(self, new_path, rpki_path):
            time.sleep(30)
            while self._get_row_count(headers) < total_rows:
                print(total_rows)
                print(self._get_row_count(headers))
                time.sleep(30)
            # optimization for later make this total rows for the page size,
            # 10 mil is just excessively large
            url = "http://localhost:8080/api/bgp/?pageSize=10000000"
            json_stuff = utils.get_json(url, headers)
            
            csv_rows = [
                self._format_asn_dict(x) for x in json_stuff["data"]]
            validity_csv_path = "{}/validity.csv".format(self.csv_dir)
            utils.write_csv(self.logger,
                            csv_rows,
                            validity_csv_path,
                            files_to_delete=new_path)
        utils.csv_to_db(self.logger,
                        Validity_Table(self.logger),
                        validity_csv_path)
        # This is misleading, this really drops the table
#        unique_p_o._create_tables()# Do this in a separate process elsewher
        unique_p_o.close()
        validity_table = Validity_Table(self.logger)
        validity_table.create_index()
        # Query the json and make a table from it
        # make an index like the one on hijack
        # do sql queries in word doc for policy4


        # Delete table
        # delete csv and gz files



#        self.run_simple_time_heuristic()
#        self.run_enforce_invalid_asn_only()
#        self.run_enforce_invalid_length_only()
#        self.run_enfore_invalid()
#        self.run_pass_if_no_alternative()
#        self.run_pass_if_no_alternative_including_superprefixes()

    @error_catcher()
    def _format_asn_dict(self, asn):
        validity = {"VALID": 1,
                    "UNKNOWN": 0,
                    "INVALID_LENGTH": -1,
                    "INVALID_ASN": -2}
        return [int(asn["asn"][2:]), asn["prefix"], validity.get(asn["validity"])]

    @error_catcher()
    def _get_row_count(self, headers):
        """Returns row count of json object for waiting"""

        try:
            return utils.get_json("http://localhost:8080/api/bgp/", headers)["metadata"]["totalCount"]
        except Exception as e:
            self.logger.warning("Problem with getting json: {}".format(e))
            return 0

    @error_catcher()
    @run_policy()
    def run_simple_time_heuristic(self):
        """Makes policy decision based on age of announcements

        For more in depth explanation, read README"""

        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_enforce_invalid_asn_only(self):
        """Makes policy decision based on validity of asn

        For more in depth explanation, read README"""

        db = Database()
        # Gets list of all asns from hijack blocked invalid asns
        sql = """CREATE TABLE invalid_asn_hijacked_blocked
                 AS SELECT exr2.asn FROM validity v, hijack h,
                 extrapolation_results2 exr2
                 WHERE v.validity = -2 AND
                 h.more_specific_prefix = v.prefix AND
                 h.more_specific_prefix = exr2.prefix AND
                 h.detected_origin_number = v.asn AND
                 h.detected_origin_number = exr2.origin;"""
        db.cursor.execute(sql)
        # Reformats the table
        sql = """CREATE TABLE invalid_asn_hijacked_blocked_final
                 AS SELECT hbd.asn, count(*) AS total
                 FROM invalid_asn_hijacked_blocked hb LEFT JOIN (
                 SELECT DISTINCT * FROM invalid_asn_hijacked_blocked) hbd
                 ON hbd.asn = hb.asn GROUP BY hbd.asn;"""
        self.cursor.execute(sql)
        # Drops the old table
        sql = """DROP TABLE invalid_asn_hijacked_blocked;"""
        db.cursor.execute(sql)

        # Gets the hijacked and not blocked

        # Gets all the asns that are hijacked and blocked with invalid asn
        sql = """CREATE TABLE invalid_asn_hijacked_not_blocked
                 AS SELECT exr2.asn FROM validity v, hijack h,
                 extrapolation_results2 exr2
                 WHERE h.more_specific_prefix = v.prefix AND
                 h.more_specific_prefix = exr2.prefix AND
                 h.detected_origin_number = v.asn AND
                 h.detected_origin_number = exr2.origin AND v.validity >= 0;"""
        db.cursor.execute(sql)
        # Gets the count of each asn
        sql = """CREATE TABLE invalid_asn_hijacked_not_blocked_final
                 AS SELECT hnbd.asn, count(*) AS total
                 FROM invalid_asn_hijacked_not_blocked  hnb LEFT JOIN (
                 SELECT DISTINCT * FROM invalid_asn_hijacked_not_blocked) hnbd
                 ON hnbd.asn = hnb.asn GROUP BY hnbd.asn;"""
        db.cursor.execute(sql)
        # Drops the old table
        sql = "DROP TABLE invalid_asn_hijacked_not_blocked;"
        self.cursor.execute(sql)

        # Gets the not hijacked and not blocked
        
        # Gets a list of all the asns hijacked and blocked
        sql = """CREATE TABLE invalid_asn_not_hijacked_blocked
                 AS SELECT exr2.asn FROM validity v, hijack h,
                 extrapolation_results2 exr2
                 WHERE v.validity = -2 AND
                 h.detected_origin_number != v.asn AND
                 v.prefix = exr2.prefix AND
                 v.asn = exr2.origin;"""
        db.cursor.execute(sql)
        # Gets the count of al the asns in the previous list
        sql = """CREATE TABLE invalid_asn_not_hijacked_blocked_final
                 AS SELECT nhbd.asn, count(*) AS total
                 FROM invalid_asn_not_hijacked_blocked nhb LEFT JOIN (
                 SELECT DISTINCT * FROM invalid_asn_not_hijacked_blocked) nhbd
                 ON nhbd.asn = nhb.asn GROUP BY nhbd.asn;"""
        db.cursor.execute(sql)
        # Drops the old table
        db.cursor.execute("DROP TABLE  invalid_asn_not_hijacked_blocked;")

        # Gets the not hijacked and not blocked table
        
        # Gets the list of asns not hijacked and blocked
        #TODO: can optimize based on subtraction of other tables
        sql = """CREATE TABLE invalid_asn_not_hijacked_not_blocked
                 AS SELECT exr2.asn FROM validity v, hijack h,
                 extrapolation_results2 exr2
                 WHERE v.validity >= 0 AND
                 v.prefix = exr2.prefix AND
                 v.asn = exr2.origin AND
                 h.detected_origin_number != v.asn AND
                 h.more_specific_prefix != v.prefix;"""
        db.cursor.execute(sql)
        # Gets the count of all the asns for this table
        sql = """CREATE TABLE invalid_asn_not_hijacked_not_blocked_final
                 AS SELECT nhnbd.asn, count(*) AS total
                 FROM invalid_asn_not_hijacked_not_blocked nhnb LEFT JOIN (
                 SELECT DISTINCT * FROM
                 invalid_asn_not_hijacked_not_blocked) nhnbd
                 ON nhnbd.asn = nhnb.asn GROUP BY nhnbd.asn;"""
        db.cursor.execute(sql)
        # Drops old table
        db.cursor.execute("invalid_asn_not_hijacked_not_blocked;")

        # Combines all of the tables into the website table data
        sql = """CREATE TABLE policy_2 AS SELECT 
                 v.asn as asn, hb.total AS hijack_blocked,
                 hnb.total AS hijack_not_blocked,
                 nhb.total AS not_hijacked_blocked,
                 nhnb.total as not_hijacked_not_blocked,
                 urls.url_list
                 FROM invalid_asn_hijacked_blocked_final hb,
                 invalid_asn_hijacked_not_blocked_final hnb,
                 invalid_asn_not_hijack_blocked nhb,
                 invalid_asn_not_hijack_not_blocked nhnb,
                 validity v,
                    (SELECT ARRAY(SELECT url FROM hijack h
                    WHERE h.detected_origin_number = v.asn)
                AS url_list) urls WHERE 
                nhnb.asn = v.asn OR
                nhb.asn = v.asn OR
                hnb.asn = v.asn OR
                hb.asn = v.asn;"""
        
    @error_catcher()
    @run_policy()
    def run_enforce_invalid_length_only(self):
        """Makes policy decision based on validity of length

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_enfore_invalid(self):
        """Makes policy decision based on validity of length or asn

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_pass_if_no_alternative(self):
        """Allows announcement only if no alternative exists

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

    @error_catcher()
    @run_policy()
    def run_pass_if_no_alternative_including_superprefixes(self):
        """Allows anouncement if no alternative/superprefix exists

        For more in depth explanation, read README"""
        return
        return rows, csv_path, table

########################
### Helper Functions ###
########################

    def _serve_file(self, path):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        os.chdir("/tmp/")
        socketserver.TCPServer(("", 8000), Handler).serve_forever()

    def _gzip_file(self, path):
        """Gzips the validator.txt file"""

        with open(path, 'rb') as f_in, gzip.open('{}.gz'.format(path), 'wb') as f_out:
            f_out.writelines(f_in)
