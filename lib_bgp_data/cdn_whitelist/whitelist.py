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

import logging
import time
import resource

from requests import Session

from ..base_classes.parser import Parser
from ..utils import utils
from .tables import Whitelist_Table

class Whitelist(Parser):
    # self.path, self.csv_dir, and self.run()
    
    def _run(self):
        api = 'http://stat.ripe.net/data/ris-asns/data.json?list_asns=true'
        asn_lookup = 'https://stat.ripe.net/data/as-overview/data.json?resource=AS'

        whitelist = []
        logging.warning('HEELO>?????????') 
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',}
        s = Session()
        s.headers.update(headers)
        r = s.get(api)
        r.raise_for_status()
        enc = r.apparent_encoding
        logging.warning(enc)
        data = r.json()
        r.close()

        asns = data['data']['asns']

        #count = 0
        #start = time.time()

        asns = [asn_lookup + str(n) for n in asns]

        resource.setrlimit(resource.RLIMIT_NOFILE, (110000, 110000))
        logging.warning('started')
        results = grequests.map((grequests.get(u) for u in asns))

        print(results)

        for result in results:
            if 'holder' in result.keys():
                if 'cloudflare' in data['holder'].lower():
                    whitelist.append(data['resource'])


"""        for asn in asns:
            r = s.get(asn_lookup + str(asn))
            r.raise_for_status()
            r.encoding = 'ascii'
            info = r.json()
            r.close()
            data = info['data']
            if 'holder' in data.keys():
                if 'cloudflare' in data['holder'].lower():
                    whitelist.append(asn)
            count += 1
            if count % 50 == 0:
                logging.warning('Running: ', count)
                elapsed = time.time() - start
                logging.warning(f'Took {elapsed} for 50 ASNs')

        logging.warning(whitelist)
"""
"""        asns = []
        api_endpoint = 'https://www.peeringdb.com/api/net?info_type=Content&depth=1'
        # pagination is required because limit of 250 per request
        count = 0
        while True:
            r = requests.get(api_endpoint + f'&skip={count}')
            r.raise_for_status()
            data = r.json()
            r.close()
            # no more data returned
            if not data['data']:
                break
            count += 250

            for network in data['data']:
                if len(network['netixlan_set']) > 50:
                    asns.append([network['name'], network['asn']])
            
        utils.rows_to_db(asns, os.path.join(self.csv_dir, 'whitelist.csv'), Whitelist_Table, clear_table=True)
"""                    
