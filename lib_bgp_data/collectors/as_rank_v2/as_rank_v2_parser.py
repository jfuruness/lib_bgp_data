#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains AS_Rank_V2 which parses AS Rank data using the Restful API

see: https://github.com/jfuruness/lib_bgp_data/wiki/AS-Rank-Parser"""


__author__ = "Nicholas Shpetner"
__credits__ = ["Nicholas Shpetner"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Production"

import os
import json
import urllib.request
import time

from .tables import AS_Rank_V2

from ...utils import utils
from ...utils.base_classes import Parser


class AS_Rank_Parser_V2(Parser):
    """Parses the AS rank data from https://asrank.caida.org/

    For a more in depth explanation:
    https://github.com/jfuruness/lib_bgp_data/wiki/AS-Rank-Parser
    """

    __slots__ = []

    #TODO: Modify this, use as base URL
    url_base = 'https://api.asrank.caida.org/v2/restful/'
    header_base = {'accept': 'application/json'}

    def _run(self, first_rank = None, last_rank = None):
        """Parses the AS rank data from https://asrank.caida.org/

        For a more in depth explanation:
        nick add a link
        """

        # Clear the table before every run
        with AS_Rank_V2(clear=True) as db:
            pass

        if first_rank is not None and last_rank is not None:
            assert last_rank > first_rank

        next_page = True
        first = 10000
        offset = 0
        count = 1
        if first_rank is not None:
            offset = first_rank
            count = first_rank

        if last_rank is not None:
            if (last_rank - first_rank) < 10000:
                first = last_rank - first_rank + 1
        
        rows = []

        while(next_page):
            url = self.url_base + f"asns/?first={first}&offset={offset}"
            req = urllib.request.Request(url, None, self.header_base)
            with urllib.request.urlopen(req) as response:
                page = response.read()
                data = json.loads(page.decode('utf-8'))

                for asn in data['data']['asns']['edges']:
                    node = asn['node']
                    asn = int(node['asn'])
                    rank = int(node['rank'])
                    links = self._get_links(asn)
                    print(f'Adding {asn} which is the {count}th asn')
                    rows.append([rank, asn, node['asnName'], links])
                    count += 1

                if data['data']['asns']['pageInfo']['hasNextPage'] == False:
                    next_page = False
                    #for debugging
                    print('Hit last page, aborting')
                    print(f'First = {first} offset = {offset}')
                if last_rank is not None:
                    if count >= last_rank:
                        next_page = False
                    elif (first + count) >= last_rank:
                        first = last_rank - count + 1 
                offset += count

        path = os.path.join(self.csv_dir, 'as_rank_v2.csv')
        utils.rows_to_db(rows, path, AS_Rank_V2, clear_table = False)

    def _get_links(self, asn):
        offset = 0
        first = 1000
        next_page = True

        # Can't use a python array due to psql not accepting it easy
        rows = '{'

        while(next_page):
            url = self.url_base + f"asnLinks/{asn}?first={first}&offset={offset}"
            req = urllib.request.Request(url, None, self.header_base)
            with urllib.request.urlopen(req) as response:
                page = response.read()
                data = json.loads(page.decode('utf-8'))
                if data['data']['asnLinks']['edges'] == []:
                    return '{}'
                for link in data['data']['asnLinks']['edges']:
                    rows += link['node']['asn1']['asn'] + ','
                if data['data']['asnLinks']['pageInfo']['hasNextPage'] == False:
                    rows = rows[:-1] + '}'
                    return rows
                else:
                    offset = offset + 1000
