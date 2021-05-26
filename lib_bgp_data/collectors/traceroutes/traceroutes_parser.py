#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains Traceroutes Parser

The purpose of this class is to download traceroutes
from ripe atlas and insert them
into a database. See README for in depth explanation
"""

__authors__ = ["Cameron Morris", "Justin Furuness"]
__credits__ = ["Cameron Morriss", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import json
import requests

from ...utils.base_classes import Parser
from ...utils import utils


class Traceroutes_Parser(Parser):
    """This class downloads traceroutes from ripe atlas"""

    url = 'https://atlas.ripe.net/api/v2/measurements/'

    def _run(self, start=utils.get_default_start(), end=utils.get_default_end()):
        print(start)
        print(end)
        ##############
        # print("Make measurement id in ripe atlas")
        ### input measurement_id = input("input measurement_id")
        measurement_id = 30330510

        print("FIXi!! THERE IS NO END!!!")
        result = json.loads(requests.get(f"{self.url}{measurement_id}/results/"
                                         f"?start={start}&format=json").text)


        print(utils.now())
        # There are three traces every time
        traces_per_route = 3
        router_paths = [[] for i in range(traces_per_route)]
        # 0 because we are just doing a single trace
        for hop in result[0]['result']:
            assert len(hop['result']) <= traces_per_route, hop['result']
            for i, trace in enumerate(hop['result']):
                #for key in trace.keys():
                #    assert key in ["from", "ttl", "size", "tos", "rtt", "x", "icmpext"], key
                #input(trace)
                router_paths[i].append(trace.get("from", None))
        print(router_paths)
        print(utils.now())
        # Map each path to ASN, collapse all repeats
        # To do this first we input all prefixes/ip addresses into a table in sql

        # Then we convert them by joining on the distinct prefix origin pairs

        # Then we remove all that are not the most specific

        # Then we extract them

        # Then we save the results
