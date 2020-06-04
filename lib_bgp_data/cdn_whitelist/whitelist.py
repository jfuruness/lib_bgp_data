#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This submodule uses PeeringDB's API to generate a whitelist of ASNs that
belong to major CDNs. The selection of CDNs is quite arbitrary: CDNs with at
least 50 exchanges are included.
"""

__authors__ = ["Tony Zheng"]
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import requests
from ..utils import utils
from .tables import Whitelist_Table

class Whitelist:
    
    def run(self):
        asns = []
        api_endpoint = 'https://www.peeringdb.com/api/net?info_type=Content&depth=1'
        # pagination is required because limit of 250 per request
        count = 0
        while True:
            r = requests.get(api_endpoint + f'&skip={count}')
            r.raise_for_status()
            data = r.json()
            # no more data returned
            if not data['data']:
                break
            count += 250

            for network in data['data']:
                if len(network['netixlan_set']) > 50:
                    asns.append([network['name'], network['asn']])
            
        utils.rows_to_db(asns, '/dev/shm/whitelist.csv', Whitelist_Table, clear_table=True)
                    
if __name__=='__main__':
    Whitelist().run()
