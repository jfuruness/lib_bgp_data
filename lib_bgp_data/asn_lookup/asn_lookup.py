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

import requests


def asn_lookup(asn: int) -> dict:

    assert type(asn) is int, "Not a number"

    # load the country code to continent mapping
    continent_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
        'continent.json') 
    with open(continent_path, 'r') as f:
        c2c_map = json.load(f)

    api = 'https://api.bgpview.io/asn/'
    r = requests.get(api + str(asn))
    r.raise_for_status()
    data = r.json()['data']
    r.close()

    country = data['country_code']
    continent = c2c_map[country] if country else None
    org = data['description_short']

    # should it return None or an empty string?    
    return {'country': country, 'continent': continent, 'org': org}


