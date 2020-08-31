#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Returns a list of the holding organization, countries, and continents for a
list of ASNs.

Using MaxMind database of CSVs which are updated weekly. But an account
sign-up is necessary to download them, making the process manual.
The benefit is that because they're CSVs, there is no ratelimit.

RIPE has an API with no ratelimit but it doesn't have good endpoints that
return country and continent data. As a matter of fact, RIPE directly
endorses MaxMind on their docs
"""

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng, Reynaldo Morris"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pandas as pd


def asn_lookup(asns: list):

    infos = []

    # pandas to read the multiple csvs used
    # I renamed the csvs because the original names were extremely long
    asn_data = pd.read_csv('./ASN/ipv4.csv')
    geo_data = pd.read_csv('./Country/country-ipv4.csv')

    # keep_default_na must be turned off or else it interprets the
    # abbr 'NA' for 'North America' as not a value
    country_data = pd.read_csv('./Country/country-english.csv',
                                keep_default_na=False)

    for asn in asns:
        # list of country and continent tuples
        CC = []
        rows = asn_data.loc[asn_data['autonomous_system_number'] == int(asn)]

        for index, row in rows.iterrows():
            org = row['autonomous_system_organization']
            prefix = row['network']

            geo_row = geo_data.loc[geo_data['network'] == prefix]

            # some prefixes are not present
            if not geo_row.empty:
                gid = geo_row['geoname_id'].values[0]
                country_row = country_data.loc[country_data['geoname_id'] \
                                                == int(gid)]
                country = country_row['country_iso_code'].values[0]
                continent = country_row['continent_code'].values[0]
                CC.append((country, continent))

        infos.append({'org': org, 'country_continent': CC})

    return infos

if __name__ == '__main__':
    print(asn_lookup(['13335']))


