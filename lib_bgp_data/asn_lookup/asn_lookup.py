#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Returns the country, continent, and holding organization of an ASN.

The mapping of country codes to continents is retrieved from:
http://country.io/continent.json

The BGPView API for ASN lookup is used because it returns an easy-to-use json.
https://bgpview.docs.apiary.io/#

The alternatives are:

RIRs RDAP service but the results are inconsistent. Compare these 2 results:

https://rdap.apnic.net/autnum/38369
https://rdap.arin.net/registry/autnum/13335

The first has a country value, the second does not.

Try RIPE's database query service:
https://apps.db.ripe.net/db-web-ui/query

On Cloudfare AS13335, no country is returned. And an inverse lookup is not
allowed since it's not registered by RIPE but by ARIN.

https://ipinfo.io/
Is promising but it's paid.

Thus all these options are incomplete, even BGPView, such as this:
https://api.bgpview.io/asn/38369

But it is the simplest and robust enough to use.
"""

import os
import json
import time

import requests


def asn_lookup(asns: list):

    info = []
    continent_list = ['AS', 'EU', 'AF', 'NA', 'OC', 'SA', 'AN']

    # load the country code to continent mapping
    continent_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  'continent.json') 
    with open(continent_path, 'r') as f:
        c2c_map = json.load(f)


    api = 'https://api.bgpview.io/asn/'

    count = 0

    with requests.Session() as session:
        for asn in asns:
            response = session.get(api + str(asn))

            # if there's no response, wait for one hour then try again
            # trying to circumvent any rate limit
            if response.status_code != 200 and len(info) < 70800:
                print('An error that was not a rate limit occurred!')
                print('HTTP: ', response.status_code)
                print('count:', count)
                time.sleep(120)
                response = session.get(api + str(asn))
                try:
                    response.raise_for_status()
                except:
                    print('Still not working.')
                    raise

            else:
                print('Hit the limit at: ', count)
                # wait for one hour
                time.sleep(3600)
                response = session.get(api + str(asn))
                if response.status_code == 429:
                    raise ValueError('Not long enough')
                
            # response.raise_for_status()

            data = response.json()['data']
            country = data['country_code']

            # sometimes they list a continent as the country
            if country in continent_list:
                country = None
                continent = country
            
            continent = c2c_map[country] if country else None
            org = data['description_short']

            info.append({'country': country,
                         'continent': continent,
                         'org': org})

            count += 1
            if count % 100 == 0:
                print(count)


if __name__ == '__main__':
    r = requests.get('https://stat.ripe.net/data/ris-asns/data.json?list_asns=true')
    asns = r.json()['data']['asns']
    asn_lookup(asns)





